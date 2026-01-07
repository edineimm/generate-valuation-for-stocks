import numpy as np
import pandas as pd
import yfinance as yf

def valuation_via_roe_cagr3_df(
    file_path: str,
    ke: float = 0.15,
    g_perpetuidade: float = 0.05,
    anos_crescimento: int = 10
) -> dict:
    """
    Valuation via ROE usando CAGR (3 anos) de:
    - LPA
    - ROE
    - Dividend Yield (DY)
    
    DataFrame esperado:
    linhas = indicadores | colunas = anos (mais recente à esquerda)
    """
    
    arquivo = file_path
    df = pd.read_csv(arquivo, sep=';', encoding='utf-8', index_col=0)
    df = df.drop(columns=["2025"], errors="ignore")
    # -------------------------------------------------
    # 1. LIMPEZA DOS DADOS
    # -------------------------------------------------
    df_clean = df.copy()

    def to_float(x):
        if pd.isna(x) or x in ["-%", "-", "%"]:
            return np.nan
        if isinstance(x, str):
            x = x.replace("%", "").replace(",", ".")
        return float(x)

    df_clean = df_clean.apply(lambda col: col.map(to_float))


    # -------------------------------------------------
    # 2. FUNÇÃO AUXILIAR: CAGR 3 ANOS
    # -------------------------------------------------
    def cagr_3_anos(series: pd.Series) -> float:
        s = series.dropna().iloc[:4]  # atual + 3 anos
        if len(s) < 4:
            return np.nan
        v_final = s.iloc[0]
        v_inicial = s.iloc[3]
        if v_inicial <= 0:
            return np.nan
        return (v_final / v_inicial) ** (1 / 3) - 1

    # -------------------------------------------------
    # 3. LPA PROJETADO (CAGR 3 ANOS)
    # -------------------------------------------------
    lpa_series = df_clean.loc["LPA"]
    lpa_atual = lpa_series.dropna().iloc[0]
    lpa_cagr = cagr_3_anos(lpa_series)

    lpa_base = lpa_atual * (1 + lpa_cagr) if not np.isnan(lpa_cagr) else lpa_atual

    # -------------------------------------------------
    # 4. ROE PROJETADO (CAGR 3 ANOS)
    # -------------------------------------------------
    roe_series = df_clean.loc["ROE"] / 100
    roe_atual = roe_series.dropna().iloc[0]
    roe_cagr = cagr_3_anos(roe_series)

    roe_base = roe_atual * (1 + roe_cagr) if not np.isnan(roe_cagr) else roe_atual
    roe_base = min(roe_base, 0.35)  # trava de realismo

    # -------------------------------------------------
    # 5. DY PROJETADO (CAGR 3 ANOS)
    # -------------------------------------------------
    dy_base = 0.0
    payout = 0.0

    if "D.Y" in df_clean.index:
        dy_series = df_clean.loc["D.Y"] / 100
        dy_atual = dy_series.dropna().iloc[0] if not dy_series.dropna().empty else 0.0
        dy_cagr = cagr_3_anos(dy_series)

        dy_base = dy_atual * (1 + dy_cagr) if not np.isnan(dy_cagr) else dy_atual

    if dy_base > 0:
        payout = min(dy_base, 0.8)

    retencao = 1 - payout

    # -------------------------------------------------
    # 6. CRESCIMENTO SUSTENTÁVEL
    # -------------------------------------------------
    g_crescimento = roe_base * retencao
    g_crescimento = min(g_crescimento, 0.25)

    # -------------------------------------------------
    # 7. PROJEÇÃO DOS LUCROS
    # -------------------------------------------------
    lucros = [
        lpa_base * (1 + g_crescimento) ** t
        for t in range(1, anos_crescimento + 1)
    ]

    # -------------------------------------------------
    # 8. VALOR PRESENTE DOS LUCROS
    # -------------------------------------------------
    vp_lucros = [
        lucro / (1 + ke) ** t
        for t, lucro in enumerate(lucros, start=1)
    ]

    # -------------------------------------------------
    # 9. VALOR TERMINAL
    # -------------------------------------------------
    lucro_terminal = lucros[-1] * (1 + g_perpetuidade)
    valor_terminal = lucro_terminal / (ke - g_perpetuidade)
    vp_valor_terminal = valor_terminal / (1 + ke) ** anos_crescimento

    # -------------------------------------------------
    # 10. VALOR INTRÍNSECO
    # -------------------------------------------------
    valor_intrinseco = sum(vp_lucros) + vp_valor_terminal

    # -------------------------------------------------
    # 11. OUTPUT
    # -------------------------------------------------
    
    tabela_valor_intrinseco = pd.DataFrame(
        {"Valor Intrínseco (R$)": [valor_intrinseco]},
        index=["Base"]
    )
    
    return tabela_valor_intrinseco.round(2) 
    
    # return {
    #     "valor_intrinseco": round(valor_intrinseco, 2),
    #     "lpa_base": round(lpa_base, 2),
    #     "roe_base_%": round(roe_base * 100, 2),
    #     "dy_base_%": round(dy_base * 100, 2),
    #     "payout_%": round(payout * 100, 2),
    #     "retencao_%": round(retencao * 100, 2),
    #     "g_crescimento_%": round(g_crescimento * 100, 2),
    #     "ke_%": round(ke * 100, 2),
    #     "g_perpetuidade_%": round(g_perpetuidade * 100, 2),
    #     "anos_crescimento": anos_crescimento
    # }


def cotation(ticket, ano):
    ticker = yf.Ticker(f"{ticket}.SA")  # ação brasileira (B3)
    
    dados = ticker.history(
        start=f"{ano-1}-12-29",
        end=f"{ano}-01-10",
        interval="1d"
    )

    # dados = ticker.history(period="1d")

    ultima_cotacao = dados['Close'].iloc[0]
    return ultima_cotacao.round(2)

def return_ticket(file, ticket):
    preco_inicio = cotation(ticket, 2025) #2026
    preco_fim = cotation(ticket, 2026) #2027
    valor_intrinceco = valuation_via_roe_cagr3_df(
        file_path=f"{file}{ticket}.csv",
        ke=0.15,
        g_perpetuidade=0.05,
        anos_crescimento=10
    ).iloc[0,0]
    
    results = {
        "ticket": ticket.upper(),
        "valor_intrinseco": valor_intrinceco.round(2),
        "desconto": ((preco_inicio - valor_intrinceco)/valor_intrinceco).round(4) * 100,
        "preco_inicio": preco_inicio.round(2),
        "preco_fim": preco_fim.round(2),
        "variacao_percentual": ((preco_fim - preco_inicio)/preco_inicio).round(4) * 100
    }
    
    return results

# Exemplo de uso

# FILE = "C:\\Users\\edine\\OneDrive\\Documentos\\stocks\\b3\\IBOV\\"
# ticket = "BBDC4"

# result = return_ticket(FILE, ticket)
# print(result)