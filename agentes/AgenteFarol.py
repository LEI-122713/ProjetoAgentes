import json
import os
import random
from core.Agente import Agente
from core.Accao import Accao


class AgenteFarol(Agente):
    def __init__(self, nome, modo="teste", ficheiro_qtable=None, epsilon=0.2, alpha=0.5, gamma=0.9, epsilon_min=0.05, epsilon_decay=0.99):
        super().__init__(nome)
        self.modo = modo  # "aprendizagem" ou "teste"
        self.q_table = {}
        self.ultimo_estado = None
        self.ultima_accao = None
        self.ficheiro_qtable = ficheiro_qtable
        # No modo teste não exploramos nem aprendemos; epsilon fica a 0.
        if self.modo == "teste":
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
        self.accoes = ["N", "S", "E", "O", "F"]
        self._carregar_politica()

    def _estado(self, obs):
        dx, dy = obs["dir_farol"]
        mov_validos = obs.get("movimentos_validos", [])

        sx = 1 if dx > 0 else -1 if dx < 0 else 0
        sy = 1 if dy > 0 else -1 if dy < 0 else 0

        # frente é a direção que mais aproxima do farol
        if abs(dx) > abs(dy):
            frente = "E" if dx > 0 else "O"
        else:
            frente = "S" if dy > 0 else "N"
        frente_livre = frente in mov_validos

        return (sx, sy, frente_livre)

    def _escolher_accao(self, estado, mov_validos):
        if self.modo == "aprendizagem" and random.random() < self.epsilon:
            # Exploração: escolhe uma ação válida aleatória (ou F)
            candidatas = [a for a in self.accoes if (a in mov_validos) or a == "F"]
            return random.choice(candidatas) if candidatas else "F"

        # Exploitação: escolhe melhor Q
        melhor_accao = None
        melhor_q = -float("inf")
        for a in self.accoes:
            if a != "F" and a not in mov_validos:
                continue
            q = self.q_table.get((estado, a), 0.0)
            if q > melhor_q:
                melhor_q = q
                melhor_accao = a

        if melhor_accao is None:
            # sem info, tenta válida ou fica
            return mov_validos[0] if mov_validos else "F"
        return melhor_accao

    def age(self):
        obs = self.ultima_observacao.dados
        estado = self._estado(obs)
        mov_validos = obs.get("movimentos_validos", [])

        accao_tipo = self._escolher_accao(estado, mov_validos)

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

        # Decaimento de exploração
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def reset(self):
        super().reset()
        self.ultimo_estado = None
        self.ultima_accao = None

    def _carregar_politica(self):
        if self.ficheiro_qtable and os.path.exists(self.ficheiro_qtable):
            with open(self.ficheiro_qtable, "r", encoding="utf-8") as f:
                dados = json.load(f)
            # Q-table guardada como dict de strings -> float
            for chave_str, valor in dados.items():
                estado_str, accao = chave_str.split("|")
                partes = estado_str.split(",")
                if len(partes) == 3:
                    sx = int(partes[0])
                    sy = int(partes[1])
                    frente_livre = partes[2] == "1"
                    estado = (sx, sy, frente_livre)
                    self.q_table[(estado, accao)] = valor

    def guardar_politica(self):
        if not self.ficheiro_qtable or self.modo == "teste":
            return
        serializado = {}
        for (estado, accao), valor in self.q_table.items():
            sx, sy, frente_livre = estado
            estado_str = f"{sx},{sy},{1 if frente_livre else 0}"
            serializado[f"{estado_str}|{accao}"] = valor

        with open(self.ficheiro_qtable, "w", encoding="utf-8") as f:
            json.dump(serializado, f, ensure_ascii=False, indent=2)
