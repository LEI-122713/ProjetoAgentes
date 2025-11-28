class MotorDeSimulacao:
    def __init__(self, ficheiro_parametros: str | None = None):
        self.agentes = []
        self.ambiente = None
        self.passo_atual = 0
        self.max_passos = 10
        self.ficheiro_parametros = ficheiro_parametros

    # --- método estático pedido no enunciado ---
    @staticmethod
    def cria(nome_do_ficheiro_parametros: str) -> "MotorDeSimulacao":
        """
        Cria e devolve uma instância de MotorDeSimulacao
        a partir de um ficheiro de parâmetros (por agora guardar só o nome).
        """
        return MotorDeSimulacao(ficheiro_parametros=nome_do_ficheiro_parametros)

    # --- listaAgentes(): Agente[] ---
    def listaAgentes(self):
        return self.agentes

    # --- executa() ---
    def executa(self):
        for t in range(self.max_passos):
            self.passo_atual += 1
            print(f"===== PASSO {self.passo_atual} =====")

            for agente in self.agentes:
                obs = self.ambiente.observacaoPara(agente)
                agente.observacao(obs)
                accao = agente.age()
                self.ambiente.agir(accao, agente)

                pos = self.ambiente.posicoes_agentes[agente]
                print(f"> {agente.nome} faz {accao.tipo} e fica em {pos}")

            self.ambiente.atualizacao()
