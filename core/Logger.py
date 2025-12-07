import json


class Logger:
    """
    Regista metricas por episodio e guarda em ficheiro.
    """

    def __init__(self):
        self.episodios = []

    def registar_episodio(self, numero, recompensa_total, passos, recompensa_descontada=0.0, sucesso=False):
        self.episodios.append({
            "episodio": numero,
            "recompensa_total": recompensa_total,
            "recompensa_descontada": recompensa_descontada,
            "passos": passos,
            "sucesso": sucesso,
        })

    def guardar(self, ficheiro="metricas.json"):
        with open(ficheiro, "w", encoding="utf-8") as f:
            json.dump(self.episodios, f, ensure_ascii=False, indent=2)

    def guardar_passos(self, historico_passos, ficheiro="metricas_passos.json"):
        """
        Guarda historico de passos (lista de dicts) em ficheiro separado.
        """
        with open(ficheiro, "w", encoding="utf-8") as f:
            json.dump(historico_passos, f, ensure_ascii=False, indent=2)
