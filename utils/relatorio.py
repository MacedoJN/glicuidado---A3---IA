import numpy as np


def gerar_estatisticas(df):

    if len(df) == 0:
        return {
            "media": 0,
            "mediana": 0,
            "desvio": 0,
            "maximo": 0,
            "minimo": 0
        }

    return {

        "media":
            np.mean(df["glicemia"]),

        "mediana":
            np.median(df["glicemia"]),

        "desvio":
            np.std(df["glicemia"]),

        "maximo":
            np.max(df["glicemia"]),

        "minimo":
            np.min(df["glicemia"])
    }
