import matplotlib.pyplot as plt
import numpy as np


class VisualizadorGrid:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.im = None
        self.textos = []
        plt.ion()

    def _mapear(self, grelha):
        mapa = {".": 0, "#": 1, "F": 2, "R": 3, "N": 4}
        mat = []
        for linha in grelha:
            mat.append([mapa.get(c, 5) for c in linha])
        return np.array(mat)

    def mostra(self, grelha):
        mat = self._mapear(grelha)
        if self.im is None:
            self.im = self.ax.imshow(mat, cmap="tab20")
        else:
            self.im.set_data(mat)
        for t in self.textos:
            t.remove()
        self.textos = []
        for y, linha in enumerate(grelha):
            for x, c in enumerate(linha):
                if c not in [".", "#"]:
                    self.textos.append(self.ax.text(x, y, c, ha="center", va="center", color="black"))
        plt.pause(0.001)
