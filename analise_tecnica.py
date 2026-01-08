import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# RSI
# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# =========================
# FUNÇÃO DE BACKTEST
# =========================
def backtest_buy_hold_timing(
    tickers,
    capital_inicial=100_000,
    start="2022-12-01",
    end="2026-01-01",
    periodo_teste=("2025-01-20", "2025-12-31"),
    plot=False
):
    resultados = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start, end=end, auto_adjust=True)
            df.columns = df.columns.get_level_values(0)

            # =========================
            # Indicadores
            # =========================
            df["MM20"] = df["Close"].rolling(20).mean()
            df["MM50"] = df["Close"].rolling(50).mean()
            df["MM200"] = df["Close"].rolling(200).mean()

            df["MM200_slope"] = df["MM200"].diff(20)

            df["RSI"] = rsi(df["Close"])
            df["RSI_prev"] = df["RSI"].shift(1)

            df["Suporte_60"] = df["Close"].rolling(60).min()
            df["Min_10"] = df["Close"].rolling(10).min()

            # =========================
            # SCORE TÉCNICO (ENTRADA)
            # =========================
            df["Score"] = 0

            # Tendência
            df.loc[df["MM200_slope"] > 0, "Score"] += 30

            # Pullback saudável
            df.loc[
                (df["Close"] < df["MM50"]) &
                (df["Close"] > df["MM200"]),
                "Score"
            ] += 25

            df.loc[
                (df["Close"] >= df["MM50"] * 0.88) &
                (df["Close"] <= df["MM50"]),
                "Score"
            ] += 15

            # RSI com reversão
            df.loc[
                (df["RSI_prev"] < 30) &
                (df["RSI"] > 30),
                "Score"
            ] += 25

            df.loc[
                (df["RSI_prev"] < 40) &
                (df["RSI"] > df["RSI_prev"]),
                "Score"
            ] += 15

            # Força compradora
            df.loc[df["Close"] > df["Close"].shift(1), "Score"] += 10
            df.loc[df["Close"] > df["Min_10"], "Score"] += 10

            # =========================
            # BACKTEST
            # =========================
            capital = capital_inicial
            posicao = 0

            preco_entrada = data_entrada = None
            preco_venda = data_venda = None

            df_test = df.loc[periodo_teste[0]:periodo_teste[1]].dropna()

            for date, row in df_test.iterrows():

                # ENTRADA
                if posicao == 0 and row["Score"] >= 80:
                    posicao = capital / row["Close"]
                    preco_entrada = row["Close"]
                    data_entrada = date
                    capital = 0

                # SAÍDA
                elif posicao > 0:
                    retorno = (row["Close"] - preco_entrada) / preco_entrada

                    sinais_venda = 0

                    if row["RSI"] > 70 and row["RSI"] < row["RSI_prev"]:
                        sinais_venda += 1

                    if row["Close"] < row["MM50"]:
                        sinais_venda += 1

                    if retorno >= 0.60 and sinais_venda >= 2:
                        capital = posicao * row["Close"]
                        preco_venda = row["Close"]
                        data_venda = date
                        posicao = 0
                        break

            capital_final = (
                posicao * df_test.iloc[-1]["Close"]
                if posicao > 0 else capital
            )

            retorno_total = (capital_final - capital_inicial) / capital_inicial
            retorno_bh = df_test.iloc[-1]["Close"] / df_test.iloc[0]["Close"] - 1

            resultados.append({
                "Ticker": ticker,
                "Compra": data_entrada.date() if data_entrada else None,
                "Venda": data_venda.date() if data_venda else None,
                "Preco_Compra": preco_entrada,
                "Preco_Venda": preco_venda,
                "Retorno_Estrategia_%": round(retorno_total * 100, 2),
                "Retorno_BuyHold_%": round(retorno_bh * 100, 2),
                "Superou_BuyHold": retorno_total > retorno_bh
            })

        except Exception as e:
            print(f"Erro no ticker {ticker}: {e}")

    return pd.DataFrame(resultados)


# =========================
# EXECUÇÃO
# =========================
tickers = ["GOOGL", "NVDA", "CRWD", "VST", "AAPL", "AVGO", "PANW", "TSLA", "TEM", "AMZN", "MSFT"]

df_resultados = backtest_buy_hold_timing(
    tickers=tickers,
    plot=False
)

print(df_resultados)