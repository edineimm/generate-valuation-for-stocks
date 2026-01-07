import pandas as pd
import numpy as np
import yfinance as yf

def get_ticker(PATH_File: str):
    arquivo = PATH_File

    # leitura do CSV
    df = pd.read_csv(
        arquivo,
        sep=";",          # separador correto
        decimal=",",      # separador decimal
        encoding="utf-8"
    )

    # obter a coluna "Código" como lista
    lista_codigos = df["Código"].dropna().tolist()
    return lista_codigos
