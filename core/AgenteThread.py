import threading
import queue


class AgenteThread(threading.Thread):
    """
    Thread que encapsula um agente. Por cada passo:
    - recebe observacao
    - devolve accao
    - recebe avaliacao (recompensa, nova obs, terminou)
    """

    def __init__(self, agente):
        super().__init__(daemon=True)
        self.agente = agente
        self.obs_queue = queue.Queue()
        self.action_queue = queue.Queue()
        self.eval_queue = queue.Queue()
        self._parar = threading.Event()

    def run(self):
        while not self._parar.is_set():
            obs = self.obs_queue.get()
            if obs is None:
                break
            self.agente.observacao(obs)
            accao = self.agente.age()
            self.action_queue.put(accao)
            avaliacao = self.eval_queue.get()
            if avaliacao is None:
                continue
            recompensa, nova_obs, terminou = avaliacao
            self.agente.avaliacaoEstadoAtual(recompensa, nova_obs, terminou)

    def passo(self, observacao):
        self.obs_queue.put(observacao)
        return self.action_queue.get()

    def avaliar(self, recompensa, nova_observacao, terminou):
        self.eval_queue.put((recompensa, nova_observacao, terminou))

    def parar(self):
        self._parar.set()
        self.obs_queue.put(None)
        self.eval_queue.put(None)
