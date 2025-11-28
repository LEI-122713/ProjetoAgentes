from core.Agente import Agente
from core.Accao import Accao

class AgenteFarol(Agente):

    def age(self):
        # A última observação deve ter um campo "dir_farol": (dx, dy)
        dx, dy = self.ultima_observacao.dados["dir_farol"]

        if abs(dx) > abs(dy):
            # Move na direção X (Este/Oeste)
            return Accao("E" if dx > 0 else "O")
        else:
            # Move na direção Y (Sul/Norte)
            return Accao("S" if dy > 0 else "N")
