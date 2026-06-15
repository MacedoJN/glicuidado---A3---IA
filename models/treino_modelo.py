import os
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Caminhos absolutos baseados na localização deste arquivo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "glicemia.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "modelo_rf.pkl")

df = pd.read_csv(CSV_PATH)

X = df[
    [
        "glicemia",
        "medicacao",
        "atividade"
    ]
]

y = (df["glicemia"] > 180).astype(int)

# Com poucos dados e classes desbalanceadas, train_test_split com
# stratify pode falhar. Tratamos esse caso de forma defensiva.
if len(df) >= 10 and y.nunique() > 1:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
else:
    # Dataset pequeno demais para split estratificado: usa tudo no treino
    X_train, y_train = X, y
    X_test, y_test = X, y

modelo = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

modelo.fit(
    X_train,
    y_train
)

os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

joblib.dump(
    modelo,
    MODEL_PATH
)

acuracia = modelo.score(X_test, y_test)
print(f"Modelo treinado com sucesso. Acurácia (amostra): {acuracia:.2f}")
print(f"Modelo salvo em: {MODEL_PATH}")
