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
            # =========================
            # Download dados
            # =========================
            df = yf.download(ticker, start=start, end=end, auto_adjust=True)
            df.columns = df.columns.get_level_values(0)

            # =========================
            # Indicadores
            # =========================
            df["MM50"] = df["Close"].rolling(50).mean()
            df["MM200"] = df["Close"].rolling(200).mean()
            df["RSI"] = rsi(df["Close"])
            df["RSI_prev"] = df["RSI"].shift(1)
            df["Topo_20"] = df["Close"].rolling(20).max()
            df["Suporte"] = df["Close"].rolling(60).min()

            # =========================
            # Score técnico (entrada)
            # =========================
            df["Score"] = 0
            df.loc[df["Close"] < df["MM200"], "Score"] += 30
            df.loc[df["Close"] > df["MM50"], "Score"] += 15
            df.loc[df["RSI"] < 40, "Score"] += 30
            df.loc[df["RSI"] < 30, "Score"] += 40
            df.loc[df["Close"] <= df["Suporte"] * 1.05, "Score"] += 25

            # =========================
            # Backtest
            # =========================
            capital = capital_inicial
            posicao = 0

            preco_entrada = data_entrada = None
            preco_venda = data_venda = None

            df_test = df.loc[periodo_teste[0]:periodo_teste[1]].dropna()

            for date, row in df_test.iterrows():

                # ENTRADA
                if posicao == 0 and row["Score"] >= 70:
                    posicao = capital / row["Close"]
                    preco_entrada = row["Close"]
                    data_entrada = date
                    capital = 0

                # SAÍDA: +80% + EXAUSTÃO
                elif posicao > 0:
                    retorno = (row["Close"] - preco_entrada) / preco_entrada

                    if retorno >= 0.80:
                        sinais_venda = 0

                        if row["RSI"] > 70 and row["RSI_prev"] > row["RSI"] and row["RSI"] < 65:
                            sinais_venda += 1

                        if row["Close"] < row["MM50"]:
                            sinais_venda += 1

                        if (row["Close"] - row["MM200"]) / row["MM200"] > 0.40:
                            sinais_venda += 1

                        if row["Close"] < row["Topo_20"]:
                            sinais_venda += 1

                        if sinais_venda >= 2:
                            capital = posicao * row["Close"]
                            preco_venda = row["Close"]
                            data_venda = date
                            posicao = 0
                            break

            # =========================
            # Capital final
            # =========================
            capital_final = (
                posicao * df_test.iloc[-1]["Close"]
                if posicao > 0 else capital
            )

            retorno_total = (capital_final - capital_inicial) / capital_inicial

            # Buy & Hold tradicional
            retorno_bh = (
                df_test.iloc[-1]["Close"] / df_test.iloc[0]["Close"] - 1
            )

            # =========================
            # Resultados
            # =========================
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

            # =========================
            # Gráfico (opcional)
            # =========================
            # if plot and not df_test.empty:
            #     plt.figure(figsize=(14,7))
            #     plt.plot(df_test.index, df_test["Close"], label="Preço", linewidth=2)
            #     plt.plot(df_test.index, df_test["MM50"], label="MM50", linestyle="--")
            #     plt.plot(df_test.index, df_test["MM200"], label="MM200", linestyle="--")
            #     plt.plot(df_test.index, df_test["Suporte"], label="Suporte", linestyle=":")

            #     if data_entrada:
            #         plt.scatter(data_entrada, preco_entrada, marker="^", s=120, label="Compra")

            #     if data_venda:
            #         plt.scatter(data_venda, preco_venda, marker="v", s=120, label="Venda +80%")

            #     plt.title(f"{ticker} – Buy & Hold com Timing Técnico – 2025")
            #     plt.legend()
            #     plt.grid(True)
            #     plt.tight_layout()
            #     plt.show()
            #     plt.close()

        except Exception as e:
            print(f"Erro no ticker {ticker}: {e}")

    return pd.DataFrame(resultados)

# tickers = ["GOOGL", "NVDA", "CRWD", "VST", "AAPL", "AVGO", "PANW", "TSLA", "TEM", "AMZN", "MSFT"]
# tickers = ["BBDC4.SA", "ITUB4.SA", "PETR4.SA", "VALE3.SA", "ABEV3.SA"]

# df_resultados = backtest_buy_hold_timing(
#     tickers=tickers,
#     plot=True
# )

# print(df_resultados)

