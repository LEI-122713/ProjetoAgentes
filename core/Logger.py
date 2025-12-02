import json


class Logger:
    """
    Regista métricas por episódio e guarda em ficheiro.
    """

    def __init__(self):
        self.episodios = []

    def registar_episodio(self, numero, recompensa_total, passos):
        self.episodios.append({
            "episodio": numero,
            "recompensa_total": recompensa_total,
            "passos": passos,
        })

    def guardar(self, ficheiro="metricas.json"):
        with open(ficheiro, "w", encoding="utf-8") as f:
            json.dump(self.episodios, f, ensure_ascii=False, indent=2)
