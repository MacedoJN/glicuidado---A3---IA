"""
Explicabilidade do modelo com **SHAP** (SHapley Additive exPlanations).

Gera figuras de explicabilidade a partir do modelo já treinado
(`models/modelo_diabetes.pkl`) e do dataset da PNS 2019:

- `docs/shap_resumo.png`   — importância média (|SHAP|) de cada feature.
- `docs/shap_beeswarm.png` — distribuição dos valores SHAP (direção e magnitude
  do efeito de cada feature em cada predição).

Diferente da importância por permutação (efeito médio global), o SHAP mostra
**como cada feature empurra a probabilidade para cima ou para baixo**, inclusive
por indivíduo — atendendo à dica de "explicabilidade" do A3.

Este script NÃO faz parte do app em produção (o `shap` é dependência apenas de
análise, em `requirements-dev.txt`). Uso:

    pip install -r requirements-dev.txt
    python models/explicar_shap.py
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib
import shap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.preprocessamento import FEATURES, separar_X_y  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "modelo_diabetes.pkl")
DOCS_DIR = os.path.join(BASE_DIR, "docs")


def main():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "Modelo não encontrado. Rode 'python models/treino_modelo.py' antes."
        )

    os.makedirs(DOCS_DIR, exist_ok=True)

    pipeline = joblib.load(MODEL_PATH)
    pre = pipeline.named_steps["preprocessamento"]
    clf = pipeline.named_steps["classificador"]

    X, _ = separar_X_y()
    # Aplica o mesmo pré-processamento do treino para explicar o classificador
    # sobre as features já transformadas (mesma ordem de FEATURES).
    X_transformado = pre.transform(X)

    print("Calculando valores SHAP...")
    explainer = shap.Explainer(clf, X_transformado, feature_names=FEATURES)
    shap_values = explainer(X_transformado)

    # 1) Importância média (barra)
    plt.figure()
    shap.plots.bar(shap_values, show=False, max_display=len(FEATURES))
    plt.title("Importância das features (SHAP) — risco de diabetes")
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "shap_resumo.png"), dpi=120, bbox_inches="tight")
    plt.close()

    # 2) Beeswarm (direção e magnitude por indivíduo)
    plt.figure()
    shap.plots.beeswarm(shap_values, show=False, max_display=len(FEATURES))
    plt.title("Efeito de cada feature na predição (SHAP)")
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "shap_beeswarm.png"), dpi=120, bbox_inches="tight")
    plt.close()

    print(f"Figuras SHAP salvas em: {DOCS_DIR}")


if __name__ == "__main__":
    main()
