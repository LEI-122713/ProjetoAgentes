from core.Ambiente import Ambiente
from core.Observacao import Observacao
from core.Accao import Accao


class AmbienteFarol(Ambiente):

    def __init__(self, largura=5, altura=5):
        super().__init__()
        self.largura = largura
        self.altura = altura
        self.posicoes_agentes = {}
        self.pos_farol = (4, 4)

    def adicionaAgente(self, agente, posicao_inicial=(0, 0)):
        self.posicoes_agentes[agente] = posicao_inicial

    def observacaoPara(self, agente):
        x, y = self.posicoes_agentes[agente]
        lx, ly = self.pos_farol

        return Observacao({
            "posicao": (x, y),
            "dir_farol": (lx - x, ly - y)
        })

    def agir(self, accao: Accao, agente):
        x, y = self.posicoes_agentes[agente]

        if accao.tipo == "N":
            y -= 1
        if accao.tipo == "S":
            y += 1
        if accao.tipo == "E":
            x += 1
        if accao.tipo == "O":
            x -= 1

        x = max(0, min(self.largura - 1, x))
        y = max(0, min(self.altura - 1, y))

        self.posicoes_agentes[agente] = (x, y)

    def atualizacao(self):
        pass
