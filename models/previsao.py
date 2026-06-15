"""
Inferência de risco de diabetes em produção.

Carrega o pipeline treinado (pré-processamento + melhor modelo) de forma lazy e
expõe funções para prever a probabilidade de diabetes a partir das features
clínicas. O mesmo pré-processamento do treino é aplicado automaticamente, pois
está encapsulado no pipeline salvo.
"""

import json
import os

import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "modelo_diabetes.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "reports", "metrics.json")

# Ordem das features esperada pelo pipeline.
FEATURES = [
    "gestacoes",
    "glicemia",
    "pressao_arterial",
    "dobra_cutanea",
    "insulina",
    "imc",
    "hist_familiar",
    "idade",
]

_modelo = None


def _carregar_modelo():
    """Carrega o pipeline apenas quando necessário (lazy loading)."""
    global _modelo

    if _modelo is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Modelo não encontrado em '{MODEL_PATH}'. "
                "Execute 'python models/treino_modelo.py' primeiro para treinar e salvar o modelo."
            )
        _modelo = joblib.load(MODEL_PATH)

    return _modelo


def prever_risco(dados: dict):
    """Prevê o risco de diabetes para um conjunto de features clínicas.

    Args:
        dados: dicionário com as chaves de ``FEATURES``.

    Returns:
        dict com ``classe`` (0/1), ``probabilidade`` (float 0-1) e
        ``classe_texto``.
    """
    modelo = _carregar_modelo()

    entrada = pd.DataFrame([[dados[f] for f in FEATURES]], columns=FEATURES)

    classe = int(modelo.predict(entrada)[0])
    probabilidade = float(modelo.predict_proba(entrada)[0][1])

    return {
        "classe": classe,
        "probabilidade": probabilidade,
        "classe_texto": "Risco de diabetes" if classe == 1 else "Baixo risco",
    }


def carregar_metricas():
    """Retorna as métricas salvas pelo treino (ou None se ainda não treinado)."""
    if not os.path.exists(METRICS_PATH):
        return None
    with open(METRICS_PATH, encoding="utf-8") as f:
        return json.load(f)
