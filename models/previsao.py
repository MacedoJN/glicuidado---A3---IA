import os
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "modelo_rf.pkl")

_modelo = None


def _carregar_modelo():
    """Carrega o modelo apenas quando necessário (lazy loading)."""
    global _modelo

    if _modelo is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Modelo não encontrado em '{MODEL_PATH}'. "
                "Execute 'python models/treino_modelo.py' primeiro para treinar e salvar o modelo."
            )
        _modelo = joblib.load(MODEL_PATH)

    return _modelo


def prever(glicemia, medicacao, atividade):

    modelo = _carregar_modelo()

    entrada = pd.DataFrame(
        [[glicemia, medicacao, atividade]],
        columns=["glicemia", "medicacao", "atividade"]
    )

    resultado = modelo.predict(entrada)

    return resultado[0]
