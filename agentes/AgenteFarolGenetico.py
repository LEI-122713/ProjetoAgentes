import json
import os
import random
from core.Agente import Agente
from core.Accao import Accao


class AgenteFarolGenetico(Agente):
    """
    Agente que aprende uma política para o ambiente do Farol com um algoritmo genético.
    Cada cromossoma associa um estado (dx, dy, frente_livre) a uma ação {N,S,E,O,F}.
    """

    def __init__(
        self,
        nome,
        modo="aprendizagem",
        ficheiro_genoma=None,
        populacao=12,
        elitismo=2,
        taxa_mutacao=0.1,
        prob_cruzamento=0.7,
    ):
        super().__init__(nome)
        self.modo = modo  # "aprendizagem" ou "teste"
        self.ficheiro_genoma = ficheiro_genoma
        self.populacao_tamanho = max(2, populacao)
        self.elitismo = max(1, elitismo)
        self.taxa_mutacao = taxa_mutacao
        self.prob_cruzamento = prob_cruzamento

        self.possiveis_accoes = ["N", "S", "E", "O", "F"]
        self.estados_possiveis = [(sx, sy, frente) for sx in (-1, 0, 1) for sy in (-1, 0, 1) for frente in (False, True)]

        self.populacao = []
        self.fitnesses = []
        self.melhor_genoma = None
        self.melhor_fitness = -float("inf")
        self.indice_genoma_atual = 0
        self.avaliados_na_geracao = 0
        self.recompensa_ep = 0.0
        self.episodio_ativo = False

        self._inicializar_populacao()

    def _inicializar_populacao(self):
        genoma_inicial = self._carregar_genoma(self.ficheiro_genoma) if self.ficheiro_genoma else None

        if self.modo == "teste":
            genoma = genoma_inicial or self._novo_genoma()
            self.populacao = [genoma]
            self.fitnesses = [0.0]
            self.melhor_genoma = dict(genoma)
            self.melhor_fitness = -float("inf")
            return

        if genoma_inicial:
            self.populacao.append(genoma_inicial)
        while len(self.populacao) < self.populacao_tamanho:
            self.populacao.append(self._novo_genoma())

        self.fitnesses = [0.0 for _ in self.populacao]
        self.melhor_genoma = genoma_inicial or dict(self.populacao[0])

    def _novo_genoma(self):
        return {estado: random.choice(self.possiveis_accoes) for estado in self.estados_possiveis}

    def _carregar_genoma(self, caminho):
        if not caminho or not os.path.exists(caminho):
            return None
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        genoma = {}
        for estado_str, accao in dados.items():
            try:
                sx, sy, frente = estado_str.split(",")
                estado = (int(sx), int(sy), frente == "1")
                if accao in self.possiveis_accoes:
                    genoma[estado] = accao
            except ValueError:
                continue
        return genoma if genoma else None

    def _estado(self, obs):
        dx, dy = obs["dir_farol"]
        mov_validos = obs.get("movimentos_validos", [])
        sx = 1 if dx > 0 else -1 if dx < 0 else 0
        sy = 1 if dy > 0 else -1 if dy < 0 else 0
        frente = None
        if abs(dx) > abs(dy):
            frente = "E" if dx > 0 else "O"
        else:
            frente = "S" if dy > 0 else "N"
        frente_livre = frente in mov_validos
        return (sx, sy, frente_livre)

    def _genoma_atual(self):
        if not self.populacao:
            self.populacao = [self._novo_genoma()]
            self.fitnesses = [0.0]
        return self.populacao[self.indice_genoma_atual]

    def _acao_para_estado(self, estado, mov_validos):
        genoma = self._genoma_atual()
        accao = genoma.get(estado)
        if accao in ["N", "S", "E", "O"] and accao not in mov_validos:
            accao = None
        if accao is None:
            if mov_validos:
                accao = random.choice(mov_validos)
            else:
                accao = "F"
        return Accao(accao)

    def age(self):
        obs = self.ultima_observacao.dados
        estado = self._estado(obs)
        mov_validos = obs.get("movimentos_validos", [])
        return self._acao_para_estado(estado, mov_validos)

    def avaliacaoEstadoAtual(self, recompensa: float, nova_observacao=None, terminou: bool = False):
        self.episodio_ativo = True
        self.recompensa_ep += recompensa

    def reset(self):
        super().reset()
        self._finalizar_episodio()

    def _finalizar_episodio(self):
        if not self.episodio_ativo:
            return

        fitness = self.recompensa_ep
        self.fitnesses[self.indice_genoma_atual] = fitness

        if fitness > self.melhor_fitness:
            self.melhor_fitness = fitness
            self.melhor_genoma = dict(self._genoma_atual())

        self.avaliados_na_geracao += 1
        self.recompensa_ep = 0.0
        self.episodio_ativo = False

        if self.modo != "aprendizagem":
            self.indice_genoma_atual = 0
            return

        self.indice_genoma_atual += 1
        if self.indice_genoma_atual >= len(self.populacao):
            self._evoluir()
            self.indice_genoma_atual = 0

    def _evoluir(self):
        avaliados = list(zip(self.populacao, self.fitnesses))
        avaliados.sort(key=lambda par: par[1], reverse=True)

        if avaliados and avaliados[0][1] > self.melhor_fitness:
            self.melhor_fitness = avaliados[0][1]
            self.melhor_genoma = dict(avaliados[0][0])

        nova_populacao = [dict(g) for g, _ in avaliados[: self.elitismo]]

        while len(nova_populacao) < self.populacao_tamanho:
            p1 = self._selecionar(avaliados)
            p2 = self._selecionar(avaliados)
            filho1, filho2 = self._cruzamento(p1, p2)
            nova_populacao.append(self._mutar(filho1))
            if len(nova_populacao) < self.populacao_tamanho:
                nova_populacao.append(self._mutar(filho2))

        self.populacao = nova_populacao[: self.populacao_tamanho]
        self.fitnesses = [0.0 for _ in self.populacao]
        self.avaliados_na_geracao = 0

    def _selecionar(self, avaliados, tamanho_torneio=3):
        if not avaliados:
            return self._novo_genoma()
        candidatos = random.sample(avaliados, k=min(tamanho_torneio, len(avaliados)))
        candidatos.sort(key=lambda par: par[1], reverse=True)
        return dict(candidatos[0][0])

    def _cruzamento(self, genoma1, genoma2):
        if random.random() > self.prob_cruzamento or not genoma1 or not genoma2:
            return dict(genoma1), dict(genoma2)

        ponto = random.randint(1, len(self.estados_possiveis) - 1)
        filho1, filho2 = {}, {}
        for i, estado in enumerate(self.estados_possiveis):
            if i < ponto:
                filho1[estado] = genoma1.get(estado, random.choice(self.possiveis_accoes))
                filho2[estado] = genoma2.get(estado, random.choice(self.possiveis_accoes))
            else:
                filho1[estado] = genoma2.get(estado, random.choice(self.possiveis_accoes))
                filho2[estado] = genoma1.get(estado, random.choice(self.possiveis_accoes))
        return filho1, filho2

    def _mutar(self, genoma):
        for estado in self.estados_possiveis:
            if random.random() < self.taxa_mutacao:
                genoma[estado] = random.choice(self.possiveis_accoes)
        return genoma

    def guardar_politica(self):
        if not self.ficheiro_genoma or not self.melhor_genoma:
            return
        serializado = {f"{sx},{sy},{1 if frente else 0}": accao for (sx, sy, frente), accao in self.melhor_genoma.items()}
        with open(self.ficheiro_genoma, "w", encoding="utf-8") as f:
            json.dump(serializado, f, ensure_ascii=False, indent=2)
