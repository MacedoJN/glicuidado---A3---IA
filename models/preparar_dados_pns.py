"""
Geração do dataset de treino a partir dos microdados reais da
**Pesquisa Nacional de Saúde (PNS) 2019 — IBGE/Ministério da Saúde**.

Fonte oficial (microdados + dicionário/input):
  https://ftp.ibge.gov.br/PNS/2019/Microdados/

O arquivo bruto `PNS_2019.txt` (fixed-width, ~455 MB) NÃO é versionado. Este
script lê apenas as colunas necessárias (pelas posições do input oficial),
constrói o alvo e as features de risco de diabetes e salva um CSV enxuto em
`data/diabetes.csv`, que é o dataset efetivamente usado no treino.

Uso:
    # baixe e extraia o PNS_2019.txt em data/raw/ (ou aponte via env RAW_PNS)
    python models/preparar_dados_pns.py

Variáveis utilizadas (posições 1-based do input_PNS_2019.sas):
    Q03001 @849  Diagnóstico médico de diabetes (1=Sim, 2=Não)         -> ALVO
    C006   @108  Sexo (1=Homem, 2=Mulher)
    C008   @117  Idade em anos
    W00101 @1337 Peso medido (kg, antropometria)
    W00203 @1362 Altura medida (cm, antropometria)
    Q00201 @807  Diagnóstico de hipertensão (1=Sim, 2=Não)
    P034   @673  Praticou exercício nos últimos 3 meses (1=Sim, 2=Não)
    P050   @711  Fuma tabaco atualmente (1/2=Sim, 3=Não)
"""

import os

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.environ.get("RAW_PNS", os.path.join(BASE_DIR, "data", "raw", "PNS_2019.txt"))
CSV_SAIDA = os.path.join(BASE_DIR, "data", "diabetes.csv")

# (início, fim) 0-based, fim exclusivo — derivados das posições do input oficial.
COLSPECS = [
    (107, 108),    # C006   sexo
    (116, 119),    # C008   idade
    (672, 673),    # P034   atividade física
    (710, 711),    # P050   tabagismo
    (806, 807),    # Q00201 hipertensão
    (848, 849),    # Q03001 diabetes (alvo)
    (1336, 1341),  # W00101 peso (kg, ex.: "085.0")
    (1361, 1366),  # W00203 altura (cm, ex.: "169.0")
]
NOMES = ["C006", "C008", "P034", "P050", "Q00201", "Q03001", "W00101", "W00203"]


def main():
    if not os.path.exists(RAW_PATH):
        raise FileNotFoundError(
            f"Arquivo bruto da PNS não encontrado em '{RAW_PATH}'.\n"
            "Baixe de https://ftp.ibge.gov.br/PNS/2019/Microdados/Dados/ "
            "(PNS_2019_*.zip), extraia o PNS_2019.txt e coloque em data/raw/ "
            "ou aponte o caminho via a variável de ambiente RAW_PNS."
        )

    print("Lendo microdados da PNS 2019 (apenas colunas necessárias)...")
    partes = []
    for chunk in pd.read_fwf(
        RAW_PATH, colspecs=COLSPECS, names=NOMES, dtype=str, chunksize=50000
    ):
        partes.append(chunk)
    bruto = pd.concat(partes, ignore_index=True)
    print(f"  linhas lidas: {len(bruto):,}")

    df = pd.DataFrame()
    df["idade"] = pd.to_numeric(bruto["C008"], errors="coerce")
    df["sexo"] = pd.to_numeric(bruto["C006"], errors="coerce")        # 1=Homem, 2=Mulher
    df["peso"] = pd.to_numeric(bruto["W00101"], errors="coerce")      # kg
    df["altura"] = pd.to_numeric(bruto["W00203"], errors="coerce")    # cm
    df["hipertensao_raw"] = pd.to_numeric(bruto["Q00201"], errors="coerce")
    df["atividade_raw"] = pd.to_numeric(bruto["P034"], errors="coerce")
    df["tabaco_raw"] = pd.to_numeric(bruto["P050"], errors="coerce")
    df["diabetes_raw"] = pd.to_numeric(bruto["Q03001"], errors="coerce")

    # Mantém apenas quem respondeu ao módulo individual e fez antropometria.
    df = df[df["diabetes_raw"].isin([1, 2])]
    df = df.dropna(subset=["idade", "sexo", "peso", "altura",
                           "hipertensao_raw", "atividade_raw", "tabaco_raw"])

    # Faixas plausíveis (remove erros de medição).
    df = df[(df["idade"].between(18, 110))
            & (df["peso"].between(30, 300))
            & (df["altura"].between(100, 220))]

    # Engenharia de atributos.
    altura_m = df["altura"] / 100.0
    df["imc"] = (df["peso"] / (altura_m ** 2)).round(1)
    df = df[df["imc"].between(12, 70)]

    saida = pd.DataFrame()
    saida["idade"] = df["idade"].astype(int)
    saida["sexo"] = (df["sexo"] == 1).astype(int)                 # 1=Masculino, 0=Feminino
    saida["imc"] = df["imc"]
    saida["hipertensao"] = (df["hipertensao_raw"] == 1).astype(int)
    saida["atividade_fisica"] = (df["atividade_raw"] == 1).astype(int)
    saida["tabagismo"] = (df["tabaco_raw"].isin([1, 2])).astype(int)
    saida["diabetes"] = (df["diabetes_raw"] == 1).astype(int)     # ALVO

    os.makedirs(os.path.dirname(CSV_SAIDA), exist_ok=True)
    saida.to_csv(CSV_SAIDA, index=False)

    pos = int(saida["diabetes"].sum())
    print(f"\nDataset salvo em: {CSV_SAIDA}")
    print(f"  registros: {len(saida):,}")
    print(f"  com diabetes: {pos:,} ({pos / len(saida):.1%})")
    print(f"  features: {[c for c in saida.columns if c != 'diabetes']}")


if __name__ == "__main__":
    main()
