import json
import os
import random
from core.Agente import Agente
from core.Accao import Accao


def _dist_manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


class AgenteForaging(Agente):
    """
    Agente de Foraging com Q-learning e modo fixo (heuristica).
    """

    def __init__(
        self,
        nome,
        modo="teste",
        ficheiro_qtable=None,
        epsilon=0.2,
        alpha=0.5,
        gamma=0.9,
        epsilon_min=0.05,
        epsilon_decay=0.99,
    ):
        super().__init__(nome)
        self.modo = modo  # "aprendizagem", "teste" ou "fixo"
        self.q_table = {}
        self.ultimo_estado = None
        self.ultima_accao = None
        self.ficheiro_qtable = ficheiro_qtable
        if self.modo in ["teste", "fixo"]:
            self.epsilon = 0.0
            self.epsilon_min = 0.0
            self.epsilon_decay = 1.0
            self.alpha = 0.0
        else:
            self.epsilon = epsilon
            self.epsilon_min = epsilon_min
            self.epsilon_decay = epsilon_decay
            self.alpha = alpha
        self.gamma = gamma
        self.accoes = ["N", "S", "E", "O", "F", "APANHAR", "DEPOSITAR"]
        self._carregar_politica()

    def _estado(self, obs):
        """
        Estado compacto: posicao (x,y), a_carregar, recurso_aqui, ninho_aqui,
        direcao do recurso mais proximo em sinais (dx_sign, dy_sign).
        """
        pos = obs["posicao"]
        recursos = obs.get("recursos", [])
        ninhos = obs.get("ninhos", [])
        a_carregar = obs.get("a_carregar", False)

        recurso_aqui = 1 if pos in recursos else 0
        ninho_aqui = 1 if pos in ninhos else 0

        dx_sign, dy_sign = 0, 0
        if recursos:
            alvo = min(recursos, key=lambda r: _dist_manhattan(pos, r))
            dx = alvo[0] - pos[0]
            dy = alvo[1] - pos[1]
            dx_sign = 1 if dx > 0 else -1 if dx < 0 else 0
            dy_sign = 1 if dy > 0 else -1 if dy < 0 else 0

        return (pos[0], pos[1], int(a_carregar), recurso_aqui, ninho_aqui, dx_sign, dy_sign)

    def _accao_fixa(self, obs):
        """
        Heuristica original: vai ao recurso mais perto, apanha; se a carregar vai ao ninho mais perto e deposita.
        """
        pos = obs["posicao"]
        mov_validos = obs.get("movimentos_validos", [])
        recursos = obs.get("recursos", [])
        ninhos = obs.get("ninhos", [])
        a_carregar = obs.get("a_carregar", False)

        if a_carregar:
            if pos in ninhos:
                return Accao("DEPOSITAR")
            destino = min(ninhos, key=lambda n: _dist_manhattan(pos, n)) if ninhos else pos
        else:
            if pos in recursos:
                return Accao("APANHAR")
            destino = min(recursos, key=lambda r: _dist_manhattan(pos, r)) if recursos else pos

        if destino == pos:
            return Accao("F")

        dx = destino[0] - pos[0]
        dy = destino[1] - pos[1]
        candidatos = []
        if dx > 0:
            candidatos.append("E")
        if dx < 0:
            candidatos.append("O")
        if dy > 0:
            candidatos.append("S")
        if dy < 0:
            candidatos.append("N")

        for c in candidatos:
            if c in mov_validos:
                return Accao(c)

        if mov_validos:
            return Accao(mov_validos[0])
        return Accao("F")

    def _escolher_accao(self, estado, obs):
        if self.modo == "fixo":
            return self._accao_fixa(obs).tipo

        mov_validos = obs.get("movimentos_validos", [])
        # Exploracao
        if self.modo == "aprendizagem" and random.random() < self.epsilon:
            candidatas = [a for a in self.accoes if (a in mov_validos) or a in ["F", "APANHAR", "DEPOSITAR"]]
            return random.choice(candidatas) if candidatas else "F"

        # Explotacao
        melhor_accao = None
        melhor_q = -float("inf")
        for a in self.accoes:
            if a in ["N", "S", "E", "O"] and a not in mov_validos:
                continue
            q = self.q_table.get((estado, a), 0.0)
            if q > melhor_q:
                melhor_q = q
                melhor_accao = a

        if melhor_accao is None:
            return mov_validos[0] if mov_validos else "F"
        return melhor_accao

    def age(self):
        obs = self.ultima_observacao.dados
        estado = self._estado(obs)
        accao_tipo = self._escolher_accao(estado, obs)

        self.ultimo_estado = estado
        self.ultima_accao = accao_tipo

        return Accao(accao_tipo)

    def avaliacaoEstadoAtual(self, recompensa: float, nova_observacao=None, terminou: bool = False):
        if self.modo != "aprendizagem":
            return
        if self.ultimo_estado is None or self.ultima_accao is None:
            return

        prox_estado = self._estado(nova_observacao.dados) if nova_observacao else self.ultimo_estado

        max_q_prox = 0.0
        if not terminou:
            max_q_prox = max(self.q_table.get((prox_estado, a), 0.0) for a in self.accoes)

        chave = (self.ultimo_estado, self.ultima_accao)
        q_atual = self.q_table.get(chave, 0.0)

        novo_q = q_atual + self.alpha * (recompensa + self.gamma * max_q_prox - q_atual)
        self.q_table[chave] = novo_q

        # Decaimento de exploracao
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def reset(self):
        super().reset()
        self.ultimo_estado = None
        self.ultima_accao = None

    def _carregar_politica(self):
        if self.ficheiro_qtable and os.path.exists(self.ficheiro_qtable):
            with open(self.ficheiro_qtable, "r", encoding="utf-8") as f:
                dados = json.load(f)
            for chave_str, valor in dados.items():
                estado_str, accao = chave_str.split("|")
                partes = [int(x) for x in estado_str.split(",")]
                if len(partes) == 7:
                    estado = tuple(partes)
                    self.q_table[(estado, accao)] = valor

    def guardar_politica(self):
        if not self.ficheiro_qtable or self.modo in ["teste", "fixo"]:
            return
        serializado = {}
        for (estado, accao), valor in self.q_table.items():
            estado_str = ",".join(str(x) for x in estado)
            serializado[f"{estado_str}|{accao}"] = valor

        with open(self.ficheiro_qtable, "w", encoding="utf-8") as f:
            json.dump(serializado, f, ensure_ascii=False, indent=2)
