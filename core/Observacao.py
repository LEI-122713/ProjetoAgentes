# Envelope de dados de percepcao enviados do ambiente para o agente
class Observacao:
    def __init__(self, dados=None):
        self.dados = dados or {}
