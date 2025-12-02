from core.Agente import Agente
from core.Accao import Accao


def _dist_manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


class AgenteForaging(Agente):
    """
    Política simples:
    - Se estiver a carregar, vai para o ninho mais perto e deposita.
    - Se não estiver a carregar, vai ao recurso mais perto e apanha.
    - Se bloqueado, fica.
    """

    def age(self):
        obs = self.ultima_observacao.dados
        pos = obs["posicao"]
        mov_validos = obs.get("movimentos_validos", [])
        recursos = obs.get("recursos", [])
        ninhos = obs.get("ninhos", [])
        a_carregar = obs.get("a_carregar", False)

        if a_carregar:
            if pos in ninhos:
                return Accao("DEPOSITAR")
            # ir para o ninho mais perto
            destino = min(ninhos, key=lambda n: _dist_manhattan(pos, n)) if ninhos else pos
        else:
            if pos in recursos:
                return Accao("APANHAR")
            destino = min(recursos, key=lambda r: _dist_manhattan(pos, r)) if recursos else pos

        if destino == pos:
            return Accao("F")

        dx = destino[0] - pos[0]
        dy = destino[1] - pos[1]

        # escolher passo que aproxima em manhattan e seja válido
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

        # se nenhum candidato válido, tenta qualquer válido
        if mov_validos:
            return Accao(mov_validos[0])

        return Accao("F")
