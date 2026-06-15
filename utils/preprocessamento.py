"""
Pré-processamento do dataset de diabetes (Pesquisa Nacional de Saúde — PNS 2019, IBGE).

Responsabilidades deste módulo:
- Carregar o dataset derivado dos microdados reais brasileiros (`data/diabetes.csv`,
  gerado por `models/preparar_dados_pns.py`).
- Disponibilizar um `Pipeline` de pré-processamento (imputação + padronização)
  reutilizado tanto no treino quanto na predição em produção, garantindo que os
  dados de entrada do usuário passem exatamente pelas mesmas transformações.

Features (todas coletáveis no próprio app, sem exames laboratoriais):
- idade (anos)
- sexo (1 = Masculino, 0 = Feminino)
- imc (kg/m², calculado de peso e altura)
- hipertensao (1 = Sim, 0 = Não)
- atividade_fisica (1 = Sim, 0 = Não)
- tabagismo (1 = Sim, 0 = Não)

Decisões de pré-processamento:
- Imputação pela MEDIANA: robusta a eventuais ausências/outliers.
- Padronização (StandardScaler): necessária para modelos sensíveis à escala
  (Regressão Logística, SVM); inofensiva para variáveis binárias e para árvores.
"""

import os

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Caminho absoluto baseado na localização deste arquivo (reprodutível em
# qualquer máquina / diretório de execução).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "diabetes.csv")

# Ordem das features esperada pelo modelo (também usada na predição do app).
FEATURES = [
    "idade",
    "sexo",
    "imc",
    "hipertensao",
    "atividade_fisica",
    "tabagismo",
]

ALVO = "diabetes"


def carregar_dados():
    """Carrega o dataset de diabetes (derivado da PNS 2019) a partir do CSV."""
    return pd.read_csv(CSV_PATH)


def construir_preprocessador():
    """Cria o pipeline de pré-processamento (imputação + padronização).

    Retornar um `Pipeline` permite encaixá-lo antes do classificador, de modo
    que treino e inferência compartilhem exatamente as mesmas etapas.
    """
    return Pipeline(
        steps=[
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
