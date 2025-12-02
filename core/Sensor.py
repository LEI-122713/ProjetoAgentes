class Sensor:
    """
    Sensor base. Ambientes concretos podem definir sensores que devolvem
    parte do estado para o agente.
    """

    def mede(self, ambiente, agente):
        """
        Mede algo no ambiente para o agente.
        Por omissão não faz nada.
        """
        return None
