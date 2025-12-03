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
    if len(sys.argv) != 3:
        print("Uso: python3 compare_metricas.py <metricas_aprendizagem.json> <metricas_teste.json>")
        sys.exit(1)

    m1_path = Path(sys.argv[1])
    m2_path = Path(sys.argv[2])

    if not m1_path.exists() or not m2_path.exists():
        print("Erro: ficheiro(s) de métricas não encontrados.")
        sys.exit(1)

    m1 = _carrega_metricas(m1_path)
    m2 = _carrega_metricas(m2_path)

    r1 = _resume(m1)
    r2 = _resume(m2)

    _mostra(m1_path.name, r1)
    _mostra(m2_path.name, r2)


if __name__ == "__main__":
    main()
