import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt


def carregar_metricas(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def curva(axes, x, y, titulo, ylabel):
    axes.plot(x, y, marker="o")
    axes.set_title(titulo)
    axes.set_xlabel("Episodio")
    axes.set_ylabel(ylabel)
    axes.grid(True, alpha=0.3)


def plotar_metricas(metricas, nome):
    episodios = [m.get("episodio", i + 1) for i, m in enumerate(metricas)]
    r_total = [m.get("recompensa_total", 0) for m in metricas]
    r_desc = [m.get("recompensa_descontada", 0) for m in metricas]
    passos = [m.get("passos", 0) for m in metricas]
    sucesso = [1 if m.get("sucesso", False) else 0 for m in metricas]
    sucesso_acum = []
    soma = 0
    for i, s in enumerate(sucesso, 1):
        soma += s
        sucesso_acum.append(soma / i)

    fig, axs = plt.subplots(2, 2, figsize=(10, 8))
    curva(axs[0, 0], episodios, r_total, f"{nome} - Recompensa total", "Recompensa")
    curva(axs[0, 1], episodios, r_desc, f"{nome} - Recompensa descontada", "Recompensa desc.")
    curva(axs[1, 0], episodios, passos, f"{nome} - Passos", "Passos")
    curva(axs[1, 1], episodios, sucesso_acum, f"{nome} - Taxa de sucesso acum.", "Taxa")
    fig.tight_layout()
    plt.show()


def main():
    if len(sys.argv) < 2:
        print("Uso: python plot_metricas.py <metricas.json> [metricas2.json ...]")
        sys.exit(1)

    for caminho in sys.argv[1:]:
        path = Path(caminho)
        if not path.exists():
            print(f"Ficheiro nao encontrado: {path}")
            continue
        metricas = carregar_metricas(path)
        plotar_metricas(metricas, path.name)


if __name__ == "__main__":
    main()
