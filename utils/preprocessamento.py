"""
Pré-processamento do dataset de diabetes (Pima Indians Diabetes Database).

Responsabilidades deste módulo:
- Carregar o dataset real (`data/diabetes.csv`).
- Tratar valores fisiologicamente impossíveis (zeros) como ausentes (NaN).
- Disponibilizar um `Pipeline` de pré-processamento (imputação + padronização)
  reutilizado tanto no treino quanto na predição em produção, garantindo que os
  dados de entrada do usuário passem exatamente pelas mesmas transformações.

Decisões de pré-processamento (justificadas no relatório/EDA):
- Glicemia, pressão arterial, dobra cutânea, insulina e IMC iguais a 0 são
  biologicamente impossíveis no contexto clínico -> tratados como ausentes.
- Imputação pela MEDIANA: robusta a outliers, comuns em dados clínicos.
- Padronização (StandardScaler): necessária para modelos sensíveis à escala
  (Regressão Logística, SVM). Não prejudica modelos baseados em árvore.
"""

import os

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

# Caminho absoluto baseado na localização deste arquivo (reprodutível em
# qualquer máquina / diretório de execução).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "diabetes.csv")

# Ordem das features esperada pelo modelo (também usada na predição do app).
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

ALVO = "diabetes"

# Colunas em que o valor 0 é fisiologicamente impossível e indica ausência.
COLUNAS_ZERO_INVALIDO = [
    "glicemia",
    "pressao_arterial",
    "dobra_cutanea",
    "insulina",
    "imc",
]


def carregar_dados():
    """Carrega o dataset bruto de diabetes a partir do CSV."""
    return pd.read_csv(CSV_PATH)


def _zeros_para_nan(X):
    """Substitui zeros inválidos por NaN nas colunas clínicas relevantes.

    Recebe e devolve um DataFrame (mantém os nomes das colunas para o
    restante do pipeline).
    """
    X = pd.DataFrame(X, columns=FEATURES).copy()
    for coluna in COLUNAS_ZERO_INVALIDO:
        X[coluna] = X[coluna].replace(0, np.nan)
    return X


def construir_preprocessador():
    """Cria o pipeline de pré-processamento (zeros->NaN, imputação, padronização).

    Retornar um `Pipeline` permite encaixá-lo antes do classificador, de modo
    que treino e inferência compartilhem exatamente as mesmas etapas.
    """
    return Pipeline(
        steps=[
            (
                "zeros_para_nan",
                FunctionTransformer(_zeros_para_nan, feature_names_out="one-to-one"),
            ),
            (
                "transformacoes",
                ColumnTransformer(
                    transformers=[
                        (
                            "num",
                            Pipeline(
                                steps=[
                                    ("imputacao", SimpleImputer(strategy="median")),
                                    ("padronizacao", StandardScaler()),
                                ]
                            ),
                            FEATURES,
                        )
                    ]
                ),
            ),
        ]
    )


def separar_X_y(df=None):
    """Separa o DataFrame em matriz de features X e vetor alvo y."""
    if df is None:
        df = carregar_dados()

    X = df[FEATURES].copy()
    y = df[ALVO].astype(int).copy()

    return X, y
