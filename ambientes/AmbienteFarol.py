from core.Ambiente import Ambiente
from core.Observacao import Observacao
from core.Accao import Accao


class AmbienteFarol(Ambiente):
    def __init__(self, largura=5, altura=5, pos_farol=None, obstaculos=None):
        super().__init__()
        self.largura = largura
        self.altura = altura
        self.posicoes_agentes = {}
        self.pos_farol = pos_farol if pos_farol else (largura - 1, altura - 1)
        self.obstaculos = set(tuple(o) for o in (obstaculos or []))
        self._terminou = False
        self.posicoes_iniciais = {}
        self._labels_agentes = {}

    def adicionaAgente(self, agente, posicao_inicial=(0, 0)):
        self.posicoes_agentes[agente] = posicao_inicial
        self.posicoes_iniciais[agente] = posicao_inicial
        # etiqueta simples e única para mostrar na grelha
        idx = len(self._labels_agentes)
        self._labels_agentes[agente] = chr(ord("A") + idx)

    def observacaoPara(self, agente):
        x, y = self.posicoes_agentes[agente]
        lx, ly = self.pos_farol

        mov_validos = self._movimentos_validos(x, y)

        return Observacao({
            "posicao": (x, y),
            "dir_farol": (lx - x, ly - y),
            "movimentos_validos": mov_validos
        })

    def _celula_livre(self, x, y):
        if x < 0 or x >= self.largura or y < 0 or y >= self.altura:
            return False
        return (x, y) not in self.obstaculos

    def _movimentos_validos(self, x, y):
        direcoes = {
            "N": (x, y - 1),
            "S": (x, y + 1),
            "E": (x + 1, y),
            "O": (x - 1, y),
        }
        return [d for d, (nx, ny) in direcoes.items() if self._celula_livre(nx, ny)]

    def _todos_no_farol(self):
        return all(pos == self.pos_farol for pos in self.posicoes_agentes.values())

    def agir(self, accao: Accao, agente):
        x, y = self.posicoes_agentes[agente]
        pos_validada = (x, y)
        dist_antes = abs(self.pos_farol[0] - x) + abs(self.pos_farol[1] - y)

        if accao.tipo == "N" and self._celula_livre(x, y - 1):
            pos_validada = (x, y - 1)
        if accao.tipo == "S" and self._celula_livre(x, y + 1):
            pos_validada = (x, y + 1)
        if accao.tipo == "E" and self._celula_livre(x + 1, y):
            pos_validada = (x + 1, y)
        if accao.tipo == "O" and self._celula_livre(x - 1, y):
            pos_validada = (x - 1, y)
        # "F" fica no sítio por definição

        self.posicoes_agentes[agente] = pos_validada

        chegou = pos_validada == self.pos_farol
        if self._todos_no_farol():
            self._terminou = True

        # recompensa base
        recompensa = 1.0 if chegou else -0.1

        # penalização extra se ficou parado ou bateu
        if pos_validada == (x, y) and not chegou:
            recompensa -= 0.1

        # shaping leve: recompensa se aproximou do farol, penalização se afastou
        if not chegou:
            dist_depois = abs(self.pos_farol[0] - pos_validada[0]) + abs(self.pos_farol[1] - pos_validada[1])
            if dist_depois < dist_antes:
                recompensa += 0.05
            elif dist_depois > dist_antes:
                recompensa -= 0.05

        return {"recompensa": recompensa, "terminou": self._terminou}

    def atualizacao(self):
        # Aqui poderíamos atualizar recursos/obstáculos; para já nada a fazer.
        pass

    def terminou(self):
        return self._terminou

    def reset(self):
        # Recoloca agentes nas posições iniciais e limpa estado de término
        for agente, pos in self.posicoes_iniciais.items():
            self.posicoes_agentes[agente] = pos
        self._terminou = False

    def render(self):
        grelha = [["." for _ in range(self.largura)] for _ in range(self.altura)]

        # Obstáculos
        for (ox, oy) in self.obstaculos:
            grelha[oy][ox] = "#"

        # Farol
        fx, fy = self.pos_farol
        grelha[fy][fx] = "F"

        # Agentes
        ocupados = {}
        for agente, (ax, ay) in self.posicoes_agentes.items():
            char = self._labels_agentes.get(agente, "A")
            chave = (ax, ay)
            if chave in ocupados:
                grelha[ay][ax] = "*"
            else:
                grelha[ay][ax] = char
                ocupados[chave] = True

        print("\n".join(" ".join(linha) for linha in grelha))
        print("---")

    def grid_state(self):
        grelha = [["." for _ in range(self.largura)] for _ in range(self.altura)]
        for (ox, oy) in self.obstaculos:
            grelha[oy][ox] = "#"
        fx, fy = self.pos_farol
        grelha[fy][fx] = "F"
        ocupados = {}
        for agente, (ax, ay) in self.posicoes_agentes.items():
            char = self._labels_agentes.get(agente, "A")
            chave = (ax, ay)
            grelha[ay][ax] = "*" if chave in ocupados else char
            ocupados[chave] = True
        return grelha
