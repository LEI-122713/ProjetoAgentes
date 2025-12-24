import json
import os
import random
from core.Agente import Agente
from core.Accao import Accao


def _dist_manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


class AgenteForagingGenetico(Agente):
    """
    Agente de Foraging com política evoluída via algoritmo genético.
    Cromossoma: mapeia estado simbólico (carregar, recurso_aqui, ninho_aqui, dx_sign, dy_sign) -> accao.
    """

    def __init__(
        self,
        nome,
        modo="aprendizagem",
        ficheiro_genoma=None,
        populacao=20,
        elitismo=4,
        taxa_mutacao=0.1,
        prob_cruzamento=0.8,
        episodios_por_individuo=1,
        bonus_sucesso=10.0,
        penalizacao_passos=0.0,
        penalizacao_distancia=0.0,
        bonus_melhoria_distancia=0.0,
        penalizacao_afastamento=0.0,
        tamanho_torneio=3,
        stall_max=2,
        heuristic_seeds=1,
    ):
        super().__init__(nome)
        self.modo = modo
        self.ficheiro_genoma = ficheiro_genoma
        self.populacao_tamanho = max(2, populacao)
        self.elitismo = max(1, elitismo)
        self.taxa_mutacao = taxa_mutacao
        self.prob_cruzamento = prob_cruzamento
        self.episodios_por_individuo = max(1, episodios_por_individuo)
        self.bonus_sucesso = bonus_sucesso
        self.penalizacao_passos = penalizacao_passos
        self.penalizacao_distancia = penalizacao_distancia
        self.bonus_melhoria_distancia = bonus_melhoria_distancia
        self.penalizacao_afastamento = penalizacao_afastamento
        self.tamanho_torneio = max(2, tamanho_torneio)
        self.stall_max = max(1, stall_max)
        self.heuristic_seeds = max(0, heuristic_seeds)

        self.possiveis_accoes = ["N", "S", "E", "O", "F", "APANHAR", "DEPOSITAR"]
        self.estados_possiveis = [
            (carry, recurso, ninho, dx, dy)
            for carry in (0, 1)
            for recurso in (0, 1)
            for ninho in (0, 1)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
        ]

        self.populacao = []
        self.fitnesses = []
        self.melhor_genoma = None
        self.melhor_fitness = -float("inf")
        self.indice_genoma_atual = 0
        self.recompensa_ep = 0.0
        self.passos_ep = 0
        self.acumulado_fitness_individuo = 0.0
        self.ep_avaliados_individuo = 0
        self.distancia_anterior = None
        self.distancia_alvo = 0
        self.teve_sucesso = False
        self.episodio_ativo = False
        self.stall_count = 0
        self.ultima_posicao = None

        self._inicializar_populacao()

    def _inicializar_populacao(self):
        genoma_inicial = self._carregar_genoma(self.ficheiro_genoma) if self.ficheiro_genoma else None
        genoma_heuristico = self._genoma_heuristico()

        if self.modo == "teste":
            genoma = genoma_inicial or genoma_heuristico or self._novo_genoma()
            self.populacao = [genoma]
            self.fitnesses = [0.0]
            self.melhor_genoma = dict(genoma)
            self.melhor_fitness = -float("inf")
            return

        if genoma_inicial:
            self.populacao.append(genoma_inicial)
        for _ in range(self.heuristic_seeds):
            if genoma_heuristico:
                self.populacao.append(dict(genoma_heuristico))

        while len(self.populacao) < self.populacao_tamanho:
            self.populacao.append(self._novo_genoma())

        self.fitnesses = [0.0 for _ in self.populacao]
        self.melhor_genoma = genoma_inicial or dict(self.populacao[0])

    def _novo_genoma(self):
        return {estado: random.choice(self.possiveis_accoes) for estado in self.estados_possiveis}

    def _genoma_heuristico(self):
        gen = {}
        for estado in self.estados_possiveis:
            gen[estado] = self._acao_heuristica(estado, todas_validas=True)
        return gen

    def _carregar_genoma(self, caminho):
        if not caminho or not os.path.exists(caminho):
            return None
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        genoma = {}
        for chave_str, accao in dados.items():
            try:
                partes = [int(x) for x in chave_str.split(",")]
                if len(partes) == 5 and accao in self.possiveis_accoes:
                    genoma[tuple(partes)] = accao
            except ValueError:
                continue
        return genoma if genoma else None

    def _guardar_genoma(self):
        if not self.ficheiro_genoma or not self.melhor_genoma:
            return
        serializado = {",".join(str(x) for x in estado): accao for estado, accao in self.melhor_genoma.items()}
        with open(self.ficheiro_genoma, "w", encoding="utf-8") as f:
            json.dump(serializado, f, ensure_ascii=False, indent=2)

    def _estado(self, obs):
        pos = obs["posicao"]
        recursos = obs.get("recursos", [])
        ninhos = obs.get("ninhos", [])
        a_carregar = 1 if obs.get("a_carregar", False) else 0

        recurso_aqui = 1 if pos in recursos else 0
        ninho_aqui = 1 if pos in ninhos else 0

        alvo = None
        if a_carregar:
            alvo = self._mais_proximo(pos, ninhos)
        else:
            alvo = self._mais_proximo(pos, recursos)
        dx_sign, dy_sign = 0, 0
        if alvo:
            dx = alvo[0] - pos[0]
            dy = alvo[1] - pos[1]
            dx_sign = 1 if dx > 0 else -1 if dx < 0 else 0
            dy_sign = 1 if dy > 0 else -1 if dy < 0 else 0
            self.distancia_alvo = _dist_manhattan(pos, alvo)
        else:
            self.distancia_alvo = 0

        return (a_carregar, recurso_aqui, ninho_aqui, dx_sign, dy_sign)

    def _mais_proximo(self, pos, alvos):
        if not alvos:
            return None
        return min(alvos, key=lambda a: _dist_manhattan(pos, a))

    def _acao_heuristica(self, estado, mov_validos=None, todas_validas=False):
        a_carregar, recurso_aqui, ninho_aqui, dx_sign, dy_sign = estado
        if mov_validos is None:
            mov_validos = []

        if a_carregar:
            if ninho_aqui:
                return "DEPOSITAR"
            preferidas = []
            if dx_sign > 0:
                preferidas.append("E")
            if dx_sign < 0:
                preferidas.append("O")
            if dy_sign > 0:
                preferidas.append("S")
            if dy_sign < 0:
                preferidas.append("N")
            for m in preferidas:
                if todas_validas or m in mov_validos:
                    return m
            return mov_validos[0] if mov_validos else "F"

        if recurso_aqui:
            return "APANHAR"
        preferidas = []
        if dx_sign > 0:
            preferidas.append("E")
        if dx_sign < 0:
            preferidas.append("O")
        if dy_sign > 0:
            preferidas.append("S")
        if dy_sign < 0:
            preferidas.append("N")
        for m in preferidas:
            if todas_validas or m in mov_validos:
                return m
        return mov_validos[0] if mov_validos else "F"

    def _acao_para_estado(self, estado, mov_validos):
        genoma = self._genoma_atual()
        accao = genoma.get(estado)

        if self.stall_count >= self.stall_max:
            heur = self._acao_heuristica(estado, mov_validos)
            if heur:
                accao = heur
            self.stall_count = 0

        if accao in ["N", "S", "E", "O"] and accao not in mov_validos:
            accao = None
        if accao is None:
            accao = self._acao_heuristica(estado, mov_validos)
        return Accao(accao)

    def _genoma_atual(self):
        if not self.populacao:
            self.populacao = [self._novo_genoma()]
            self.fitnesses = [0.0]
        return self.populacao[self.indice_genoma_atual]

    def age(self):
        obs = self.ultima_observacao.dados
        estado = self._estado(obs)
        mov_validos = obs.get("movimentos_validos", [])
        return self._acao_para_estado(estado, mov_validos)

    def avaliacaoEstadoAtual(self, recompensa: float, nova_observacao=None, terminou: bool = False):
        self.episodio_ativo = True
        self.recompensa_ep += recompensa
        self.passos_ep += 1

        if nova_observacao is not None:
            pos = nova_observacao.dados.get("posicao")
            if pos is not None:
                if self.ultima_posicao == pos:
                    self.stall_count += 1
                else:
                    self.stall_count = 0
                self.ultima_posicao = pos
            estado = self._estado(nova_observacao.dados)
            nova_dist = self.distancia_alvo
            if self.distancia_anterior is None:
                self.distancia_anterior = nova_dist
            else:
                delta = self.distancia_anterior - nova_dist
                if delta > 0 and self.bonus_melhoria_distancia > 0:
                    self.recompensa_ep += self.bonus_melhoria_distancia * delta
                if delta < 0 and self.penalizacao_afastamento > 0:
                    self.recompensa_ep -= self.penalizacao_afastamento * abs(delta)
                self.distancia_anterior = nova_dist
        if terminou:
            self.teve_sucesso = True

    def reset(self):
        super().reset()
        self._finalizar_episodio()

    def _finalizar_episodio(self):
        if not self.episodio_ativo:
            return

        fitness = self.recompensa_ep
        if self.teve_sucesso:
            fitness += self.bonus_sucesso
        if self.penalizacao_passos > 0:
            fitness -= self.penalizacao_passos * self.passos_ep
        if not self.teve_sucesso and self.penalizacao_distancia > 0:
            fitness -= self.penalizacao_distancia * self.distancia_alvo

        self.acumulado_fitness_individuo += fitness
        self.ep_avaliados_individuo += 1

        if self.ep_avaliados_individuo >= self.episodios_por_individuo:
            fitness_medio = self.acumulado_fitness_individuo / self.episodios_por_individuo
            self.fitnesses[self.indice_genoma_atual] = fitness_medio

            if fitness_medio > self.melhor_fitness:
                self.melhor_fitness = fitness_medio
                self.melhor_genoma = dict(self._genoma_atual())

            self.indice_genoma_atual += 1
            if self.indice_genoma_atual >= len(self.populacao):
                self._evoluir()
                self.indice_genoma_atual = 0

            self.acumulado_fitness_individuo = 0.0
            self.ep_avaliados_individuo = 0

        self.recompensa_ep = 0.0
        self.passos_ep = 0
        self.teve_sucesso = False
        self.episodio_ativo = False
        self.distancia_anterior = None
        self.distancia_alvo = 0
        self.stall_count = 0
        self.ultima_posicao = None

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

    def _selecionar(self, avaliados):
        if not avaliados:
            return self._novo_genoma()
        candidatos = random.sample(avaliados, k=min(self.tamanho_torneio, len(avaliados)))
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
        self._guardar_genoma()
