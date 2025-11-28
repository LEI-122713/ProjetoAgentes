from core.Simulator import Simulator
from ambientes.AmbienteFarol import LighthouseEnv
from agentes.AgenteFarol import LighthouseAgent

sim = Simulator()

env = LighthouseEnv()
ag = LighthouseAgent("A1")

sim.env = env
sim.agents.append(ag)
env.addAgent(ag, (0, 0))

sim.execute()
