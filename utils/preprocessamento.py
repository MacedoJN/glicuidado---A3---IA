import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "glicemia.csv")


def carregar_dados():

    df = pd.read_csv(CSV_PATH)

    df.dropna(inplace=True)

    return df
