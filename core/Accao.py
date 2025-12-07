# Estrutura simples para transportar o tipo de accao e parametros
class Accao:
    def __init__(self, tipo, parametros=None):
        self.tipo = tipo
        self.parametros = parametros or {}
