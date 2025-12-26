import json
import sys
from pathlib import Path


def _carrega_metricas(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def _resume(metricas):
    n = len(metricas)
    if n == 0:
        return {
            "episodios": 0,
            "recompensa_media": 0.0,
            "recompensa_descontada_media": 0.0,
            "passos_medios": 0.0,
            "taxa_sucesso": 0.0,
        }

    soma_r = sum(m.get("recompensa_total", 0.0) for m in metricas)
    soma_rd = sum(m.get("recompensa_descontada", 0.0) for m in metricas)
    soma_passos = sum(m.get("passos", 0) for m in metricas)
    sucessos = sum(1 for m in metricas if m.get("sucesso", False))

    return {
        "episodios": n,
        "recompensa_media": soma_r / n,
        "recompensa_descontada_media": soma_rd / n,
        "passos_medios": soma_passos / n,
        "taxa_sucesso": sucessos / n,
    }


def _mostra(label, resumo):
    print(f"== {label} ==")
    print(f"Episódios: {resumo['episodios']}")
    print(f"Recompensa média: {resumo['recompensa_media']:.3f}")
    print(f"Recompensa descontada média: {resumo['recompensa_descontada_media']:.3f}")
    print(f"Passos médios: {resumo['passos_medios']:.2f}")
    print(f"Taxa de sucesso: {resumo['taxa_sucesso']*100:.1f}%")
    print()


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 compare_metricas.py <metricas1.json> [metricas2.json ...]")
        sys.exit(1)

    for caminho in sys.argv[1:]:
        m_path = Path(caminho)
        if not m_path.exists():
            print(f"Erro: ficheiro de métricas não encontrado: {m_path}")
            continue
        metricas = _carrega_metricas(m_path)
        resumo = _resume(metricas)
        _mostra(m_path.name, resumo)


if __name__ == "__main__":
    main()
