# Interface base de agente (observa, decide accao, opcionalmente aprende)
class Agente:
    def __init__(self, nome: str):
        self.nome = nome
        self.ultima_observacao = None
        self.sensores = []

    # --------- interface pedida no enunciado ---------

    @staticmethod
    def cria(nome_do_ficheiro_parametros: str) -> "Agente":
        """
        Cria um agente a partir de um ficheiro de parâmetros.
        Para agentes concretos (AgenteFarol, etc.) o normal é usar
        o construtor dessas subclasses, mas esta função cumpre o interface pedido.
        """
        return Agente(nome_do_ficheiro_parametros)

    def observacao(self, obs: "Observacao"):
        """
        Recebe uma Observacao do ambiente e guarda como última observação.
        """
        self.ultima_observacao = obs

    def age(self) -> "Accao":
        """
        Decide qual a próxima Accao a executar com base na última observação.
        Deve ser implementado nas subclasses (por omissão, NotImplemented).
        """
        raise NotImplementedError

    def avaliacaoEstadoAtual(self, recompensa: float, nova_observacao=None, terminou: bool = False):
        """
        Permite ao agente atualizar a sua política com base na recompensa
        (usado no modo de Aprendizagem).
        Por omissão não faz nada; agentes com aprendizagem sobrepõem.
        """
        pass

    def reset(self):
        """
        Reinicia estado interno do agente (por exemplo, antes de um novo episódio).
        """
        self.ultima_observacao = None

    def instala(self, sensor: "Sensor"):
        """
        Instala um novo sensor no agente.
        """
        self.sensores.append(sensor)

    def comunica(self, mensagem: str, de_agente: "Agente"):
        """
        Comunicação entre agentes (podes deixar vazio se não usares).
        """
        pass
