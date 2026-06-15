"""
Treino e comparação de modelos de IA para predição de risco de diabetes.

Este script cumpre os requisitos técnicos do A3:
- Pipeline completo e reprodutível (pré-processamento + modelo encapsulados).
- Comparação de 4 algoritmos (>= 2 exigidos).
- Validação cruzada estratificada (K-Fold = 5).
- Métricas adequadas para problema clínico desbalanceado:
  accuracy, precision, recall, F1 e ROC-AUC.
- Avaliação em conjunto de teste separado: matriz de confusão e curva ROC.
- Explicabilidade via importância por permutação (model-agnostic).
- Persistência do melhor modelo, das métricas (JSON) e das figuras.

Uso:
    python models/treino_modelo.py
"""

import json
import os

import matplotlib

matplotlib.use("Agg")  # backend não-interativo: permite salvar figuras sem display

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import joblib

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

# Permite rodar tanto `python models/treino_modelo.py` quanto
# `python -m models.treino_modelo` a partir da raiz do projeto.
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.preprocessamento import (  # noqa: E402
    FEATURES,
    construir_preprocessador,
    separar_X_y,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "modelo_diabetes.pkl")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")
METRICS_PATH = os.path.join(REPORTS_DIR, "metrics.json")

RANDOM_STATE = 42

# Algoritmos comparados. Todos encapsulados com o MESMO pré-processamento,
# garantindo comparação justa.
MODELOS = {
    "Regressão Logística": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
    "Random Forest": RandomForestClassifier(
        n_estimators=200, random_state=RANDOM_STATE
    ),
    "SVM (RBF)": SVC(probability=True, random_state=RANDOM_STATE),
    "Gradient Boosting": GradientBoostingClassifier(random_state=RANDOM_STATE),
}

SCORING = ["accuracy", "precision", "recall", "f1", "roc_auc"]


def _construir_pipeline(classificador):
    """Encapsula pré-processamento + classificador em um único Pipeline."""
    return Pipeline(
        steps=[
            ("preprocessamento", construir_preprocessador()),
            ("classificador", classificador),
        ]
    )


def _validacao_cruzada(X_train, y_train):
    """Roda K-Fold estratificado para cada algoritmo e coleta as métricas médias."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    resultados = {}

    for nome, classificador in MODELOS.items():
        pipeline = _construir_pipeline(classificador)

        scores = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring=SCORING,
            return_train_score=False,
        )

        resultados[nome] = {
            metrica: float(np.mean(scores[f"test_{metrica}"])) for metrica in SCORING
        }

        print(
            f"  {nome:22s} | "
            + " | ".join(f"{m}={resultados[nome][m]:.3f}" for m in SCORING)
        )

    return resultados


def _grafico_comparacao(resultados):
    """Gera gráfico de barras comparando os algoritmos por métrica."""
    df = pd.DataFrame(resultados).T[SCORING]
    ax = df.plot(kind="bar", figsize=(11, 6), rot=15)
    ax.set_title("Comparação de Algoritmos (validação cruzada 5-fold)")
    ax.set_ylabel("Score médio")
    ax.set_ylim(0, 1)
    ax.legend(loc="lower right", ncol=len(SCORING), fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "comparacao_modelos.png"), dpi=120)
    plt.close()


def _grafico_matriz_confusao(y_test, y_pred, nome_modelo):
    """Salva a matriz de confusão do melhor modelo no conjunto de teste."""
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm, display_labels=["Sem diabetes", "Com diabetes"]
    )
    fig, ax = plt.subplots(figsize=(6, 5))
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(f"Matriz de Confusão — {nome_modelo}")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "matriz_confusao.png"), dpi=120)
    plt.close()


def _grafico_roc(y_test, y_proba, nome_modelo, auc):
    """Salva a curva ROC do melhor modelo."""
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f"{nome_modelo} (AUC = {auc:.3f})", color="#2F6FED")
    plt.plot([0, 1], [0, 1], "--", color="gray", label="Aleatório")
    plt.xlabel("Taxa de Falsos Positivos")
    plt.ylabel("Taxa de Verdadeiros Positivos")
    plt.title("Curva ROC")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "curva_roc.png"), dpi=120)
    plt.close()


def _importancia_features(pipeline, X_test, y_test):
    """Calcula a importância das features por permutação (model-agnostic)."""
    resultado = permutation_importance(
        pipeline,
        X_test,
        y_test,
        n_repeats=20,
        random_state=RANDOM_STATE,
        scoring="roc_auc",
    )
    importancias = {
        FEATURES[i]: float(resultado.importances_mean[i]) for i in range(len(FEATURES))
    }

    # Gráfico ordenado
    ordenado = dict(sorted(importancias.items(), key=lambda kv: kv[1]))
    plt.figure(figsize=(8, 5))
    sns.barplot(x=list(ordenado.values()), y=list(ordenado.keys()), color="#2F6FED")
    plt.title("Importância das Features (permutação, métrica ROC-AUC)")
    plt.xlabel("Queda média no ROC-AUC ao embaralhar a feature")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "importancia_features.png"), dpi=120)
    plt.close()

    return importancias


def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)
    sns.set_theme(style="whitegrid")

    print("Carregando dados e separando treino/teste...")
    X, y = separar_X_y()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    print("\nValidação cruzada (5-fold) — comparação de algoritmos:")
    resultados_cv = _validacao_cruzada(X_train, y_train)
    _grafico_comparacao(resultados_cv)

    # Seleciona o melhor algoritmo pelo ROC-AUC médio na validação cruzada.
    melhor_nome = max(resultados_cv, key=lambda n: resultados_cv[n]["roc_auc"])
    print(f"\nMelhor algoritmo (ROC-AUC na CV): {melhor_nome}")

    # Treina o melhor pipeline em todo o conjunto de treino e avalia no teste.
    melhor_pipeline = _construir_pipeline(MODELOS[melhor_nome])
    melhor_pipeline.fit(X_train, y_train)

    y_pred = melhor_pipeline.predict(X_test)
    y_proba = melhor_pipeline.predict_proba(X_test)[:, 1]
    auc_teste = roc_auc_score(y_test, y_proba)

    print("\nDesempenho no conjunto de teste (dados nunca vistos):")
    print(
        classification_report(
            y_test, y_pred, target_names=["Sem diabetes", "Com diabetes"]
        )
    )
    print(f"ROC-AUC (teste): {auc_teste:.3f}")

    _grafico_matriz_confusao(y_test, y_pred, melhor_nome)
    _grafico_roc(y_test, y_proba, melhor_nome, auc_teste)
    importancias = _importancia_features(melhor_pipeline, X_test, y_test)

    # Persistência
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(melhor_pipeline, MODEL_PATH)

    relatorio_teste = classification_report(
        y_test,
        y_pred,
        target_names=["Sem diabetes", "Com diabetes"],
        output_dict=True,
    )

    metricas = {
        "melhor_modelo": melhor_nome,
        "validacao_cruzada": resultados_cv,
        "teste": {
            "roc_auc": float(auc_teste),
            "accuracy": float(relatorio_teste["accuracy"]),
            "precision_positivo": float(relatorio_teste["Com diabetes"]["precision"]),
            "recall_positivo": float(relatorio_teste["Com diabetes"]["recall"]),
            "f1_positivo": float(relatorio_teste["Com diabetes"]["f1-score"]),
            "matriz_confusao": confusion_matrix(y_test, y_pred).tolist(),
        },
        "importancia_features": importancias,
        "features": FEATURES,
    }

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metricas, f, ensure_ascii=False, indent=2)

    print(f"\nModelo salvo em: {MODEL_PATH}")
    print(f"Métricas salvas em: {METRICS_PATH}")
    print(f"Figuras salvas em: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
