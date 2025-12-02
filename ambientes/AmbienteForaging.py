from core.Ambiente import Ambiente
from core.Observacao import Observacao
from core.Accao import Accao


class AmbienteForaging(Ambiente):
    """
    Grelha 2D com recursos, ninhos e obstáculos.
    Ações: N, S, E, O, F (ficar), APANHAR, DEPOSITAR.
    """

    def __init__(self, largura=7, altura=7, recursos=None, valores_recursos=None, ninhos=None, obstaculos=None):
        super().__init__()
        self.largura = largura
        self.altura = altura
        self.recursos = set(tuple(r) for r in (recursos or []))
        self.valores_recursos = self._normalizar_valores(valores_recursos or {})
        self.ninhos = set(tuple(n) for n in (ninhos or []))
        self.obstaculos = set(tuple(o) for o in (obstaculos or []))
        self.posicoes_agentes = {}
        self.agentes_carry = {}  # agente -> valor do recurso transportado (0 se vazio)
        self._terminou = False
        self._recursos_iniciais = set(self.recursos)
        self._valores_iniciais = dict(self.valores_recursos)
        self._posicoes_iniciais = {}

    def adicionaAgente(self, agente, posicao_inicial=(0, 0)):
        self.posicoes_agentes[agente] = posicao_inicial
        self.agentes_carry[agente] = 0
        self._posicoes_iniciais[agente] = posicao_inicial

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

    def _normalizar_valores(self, valores_recursos):
        """
        Converte chaves do JSON em tuplos (ex.: "[5,1]" ou "5,1" -> (5, 1)).
        """
        normalizados = {}
        for k, v in valores_recursos.items():
            if isinstance(k, (list, tuple)):
                pos = tuple(k)
            elif isinstance(k, str):
                numeros = [int(x) for x in k.replace("[", "").replace("]", "").split(",") if x.strip()]
                pos = tuple(numeros)
            else:
                continue
            if len(pos) == 2:
                normalizados[pos] = v
        return normalizados

    def observacaoPara(self, agente):
        x, y = self.posicoes_agentes[agente]
        mov_validos = self._movimentos_validos(x, y)
        recursos_visiveis = list(self.recursos)
        return Observacao({
            "posicao": (x, y),
            "movimentos_validos": mov_validos,
            "recursos": recursos_visiveis,
            "ninhos": list(self.ninhos),
            "a_carregar": self.agentes_carry.get(agente, 0) > 0,
        })

    def _todos_recursos_recolhidos(self):
        return len(self.recursos) == 0 and all(v == 0 for v in self.agentes_carry.values())

    def agir(self, accao: Accao, agente):
        x, y = self.posicoes_agentes[agente]
        recompensa = -0.1  # custo por passo

        if accao.tipo in ["N", "S", "E", "O"]:
            destino = None
            if accao.tipo == "N" and self._celula_livre(x, y - 1):
                destino = (x, y - 1)
            if accao.tipo == "S" and self._celula_livre(x, y + 1):
                destino = (x, y + 1)
            if accao.tipo == "E" and self._celula_livre(x + 1, y):
                destino = (x + 1, y)
            if accao.tipo == "O" and self._celula_livre(x - 1, y):
                destino = (x - 1, y)
            if destino:
                self.posicoes_agentes[agente] = destino
            else:
                recompensa -= 0.2  # penalização por bater em obstáculo/borda

        elif accao.tipo == "APANHAR":
            if (x, y) in self.recursos and self.agentes_carry[agente] == 0:
                self.recursos.remove((x, y))
                valor = self.valores_recursos.get((x, y), 1.0)
                self.agentes_carry[agente] = valor
                recompensa += 0.5  # pequeno bónus por apanhar
            else:
                recompensa -= 0.2

        elif accao.tipo == "DEPOSITAR":
            if (x, y) in self.ninhos and self.agentes_carry[agente] > 0:
                recompensa += self.agentes_carry[agente]
                self.agentes_carry[agente] = 0
            else:
                recompensa -= 0.2

        # "F" fica no sítio, só aplica custo do passo

        if self._todos_recursos_recolhidos():
            self._terminou = True

        return {"recompensa": recompensa, "terminou": self._terminou}

    def atualizacao(self):
        # Sem dinâmica extra por agora
        pass

    def terminou(self):
        return self._terminou

    def reset(self):
        self.recursos = set(self._recursos_iniciais)
        self.valores_recursos = dict(self._valores_iniciais)
        self._terminou = False
        for agente, pos in self._posicoes_iniciais.items():
            self.posicoes_agentes[agente] = pos
            self.agentes_carry[agente] = 0

    def render(self):
        grelha = [["." for _ in range(self.largura)] for _ in range(self.altura)]

        for (ox, oy) in self.obstaculos:
            grelha[oy][ox] = "#"

        for (rx, ry) in self.recursos:
            grelha[ry][rx] = "R"

        for (nx, ny) in self.ninhos:
            grelha[ny][nx] = "N"

        ocupados = {}
        for agente, (ax, ay) in self.posicoes_agentes.items():
            char = agente.nome[0].upper() if agente.nome else "A"
            chave = (ax, ay)
            if chave in ocupados:
                grelha[ay][ax] = "*"
            else:
                grelha[ay][ax] = char
                ocupados[chave] = True

        print("\n".join(" ".join(linha) for linha in grelha))
        print("---")
