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
        episodios_por_individuo=1,
        bonus_sucesso=8.0,
        penalizacao_passos=0.0,
        penalizacao_distancia=0.1,
        bonus_melhoria_distancia=0.5,
        penalizacao_afastamento=0.2,
        tamanho_torneio=3,
        stall_max=2,
        heuristic_seeds=1,
    ):
        super().__init__(nome)
        self.modo = modo  # "aprendizagem" ou "teste"
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
        self.passos_ep = 0
        self.teve_sucesso = False
        self.acumulado_fitness_individuo = 0.0
        self.ep_avaliados_individuo = 0
        self.distancia_anterior = None
        self.ultima_distancia = 0
        self.ultima_posicao = None
        self.stall_count = 0

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
        # semeia cromossomas heurísticos (ir sempre na direção do farol quando livre)
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
        """
        Heuristica simples: tenta mover na direcao do farol se a celula frente_livre o permitir; senao fica parado.
        """
        gen = {}
        for (sx, sy, frente_livre) in self.estados_possiveis:
            if sx == 0 and sy == 0:
                gen[(sx, sy, frente_livre)] = "F"
                continue
            if frente_livre:
                # prioridade ao eixo dominante
                if abs(sx) >= abs(sy):
                    gen[(sx, sy, frente_livre)] = "E" if sx > 0 else "O"
                else:
                    gen[(sx, sy, frente_livre)] = "S" if sy > 0 else "N"
            else:
                # se frente bloqueada, tenta outro eixo ou fica
                if sx != 0:
                    gen[(sx, sy, frente_livre)] = "S" if sy > 0 else "N" if sy < 0 else ("E" if sx > 0 else "O")
                elif sy != 0:
                    gen[(sx, sy, frente_livre)] = "E" if sx > 0 else "O"
                else:
                    gen[(sx, sy, frente_livre)] = "F"
        return gen

    def _acao_heuristica(self, estado, mov_validos):
        sx, sy, frente_livre = estado
        if sx == 0 and sy == 0:
            return "F"
        if frente_livre:
            if abs(sx) >= abs(sy):
                preferida = "E" if sx > 0 else "O"
            else:
                preferida = "S" if sy > 0 else "N"
            if preferida in mov_validos:
                return preferida
        # fallback: tenta eixo alternativo
        alternativas = []
        if sx != 0:
            alternativas.append("E" if sx > 0 else "O")
        if sy != 0:
            alternativas.append("S" if sy > 0 else "N")
        for alt in alternativas:
            if alt in mov_validos:
                return alt
        return mov_validos[0] if mov_validos else "F"

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
        if self.stall_count >= self.stall_max:
            # heuristica de desbloqueio: tenta aproximar do farol
            if mov_validos:
                accao = self._acao_heuristica(estado, mov_validos)
            self.stall_count = 0
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
        self.passos_ep += 1
        if nova_observacao is not None:
            pos = nova_observacao.dados.get("posicao")
            if pos is not None:
                if self.ultima_posicao == pos:
                    self.stall_count += 1
                else:
                    self.stall_count = 0
                self.ultima_posicao = pos
        if nova_observacao is not None:
            dx, dy = nova_observacao.dados.get("dir_farol", (0, 0))
            self.ultima_distancia = abs(dx) + abs(dy)
            if self.distancia_anterior is None:
                self.distancia_anterior = self.ultima_distancia
            else:
                delta = self.distancia_anterior - self.ultima_distancia
                if delta > 0 and self.bonus_melhoria_distancia > 0:
                    self.recompensa_ep += self.bonus_melhoria_distancia * delta
                if delta < 0 and self.penalizacao_afastamento > 0:
                    self.recompensa_ep -= self.penalizacao_afastamento * abs(delta)
                self.distancia_anterior = self.ultima_distancia
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
            fitness -= self.penalizacao_distancia * self.ultima_distancia

        self.acumulado_fitness_individuo += fitness
        self.ep_avaliados_individuo += 1

        if self.ep_avaliados_individuo >= self.episodios_por_individuo:
            fitness_medio = self.acumulado_fitness_individuo / self.episodios_por_individuo
            self.fitnesses[self.indice_genoma_atual] = fitness_medio

            if fitness_medio > self.melhor_fitness:
                self.melhor_fitness = fitness_medio
                self.melhor_genoma = dict(self._genoma_atual())

            self.avaliados_na_geracao += 1
            # modo teste: não evolui, mantém sempre o melhor genoma carregado
            if self.modo != "aprendizagem":
                self.indice_genoma_atual = 0
            else:
                self._preparar_proximo_individuo()

            # se terminámos avaliação de um indivíduo, reset contadores
            self.acumulado_fitness_individuo = 0.0
            self.ep_avaliados_individuo = 0

        self.recompensa_ep = 0.0
        self.passos_ep = 0
        self.teve_sucesso = False
        self.episodio_ativo = False
        self.distancia_anterior = None
        self.ultima_distancia = 0
        self.ultima_posicao = None
        self.stall_count = 0

    def _preparar_proximo_individuo(self):
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
        if not self.ficheiro_genoma or not self.melhor_genoma:
            return
        serializado = {f"{sx},{sy},{1 if frente else 0}": accao for (sx, sy, frente), accao in self.melhor_genoma.items()}
        with open(self.ficheiro_genoma, "w", encoding="utf-8") as f:
            json.dump(serializado, f, ensure_ascii=False, indent=2)
