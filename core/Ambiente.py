class Ambiente:
    def __init__(self):
        # Dicionário para guardar a posição de cada agente no ambiente
        # Exemplo: {agente1: (x, y), agente2: (x2, y2), ...}
        self.posicoes_agentes = {}

    def observacaoPara(self, agente):
        """
        Devolve uma Observacao para o agente dado, com base no estado atual do ambiente.
        Deve ser implementado nas subclasses (ex.: AmbienteFarol, AmbienteForaging).
        """
        raise NotImplementedError

    def agir(self, accao, agente):
        """
        Aplica a ação 'accao' do 'agente' no ambiente (mover, apanhar recurso, etc.).
        Pode devolver recompensa e/ou estado final, conforme o problema.
        """
        raise NotImplementedError

    def atualizacao(self):
        """
        Atualiza o estado global do ambiente no fim de cada passo de simulação
        (ex.: reposição de recursos, animações, etc.).
        """
        raise NotImplementedError
