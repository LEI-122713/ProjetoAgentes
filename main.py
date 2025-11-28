from core.MotorDeSimulacao import MotorDeSimulacao
from ambientes.AmbienteFarol import AmbienteFarol
from agentes.AgenteFarol import AgenteFarol

sim = MotorDeSimulacao()

env = AmbienteFarol()
ag = AgenteFarol("A1")

sim.ambiente = env
sim.agentes.append(ag)
env.adicionaAgente(ag, (0, 0))

sim.executa()
