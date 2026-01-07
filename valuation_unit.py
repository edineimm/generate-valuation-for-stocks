import pandas as pd
import numpy as np
import yfinance as yf
import holidays

def primeiro_dia_util(ano: int, pais: str = "BR"):
    """
    Retorna o primeiro dia útil do ano informado,
    considerando feriados nacionais do país.
    """
    feriados = holidays.country_holidays(pais, years=ano)

    dia_util = pd.bdate_range(
        start=f"{ano}-01-01",
        periods=1,
        holidays=feriados
    )[0]

    return dia_util.date()


def limpar_numeros(df):
    df = df.copy()

    df = (
        df.replace("-", np.nan)                  # traços → NaN
          .replace("%", "", regex=True)           # remove %
          .replace(",", ".", regex=True)          # vírgula → ponto
    )

    # converte tudo que for possível para numérico
    df = df.apply(pd.to_numeric, errors="coerce")

    return df

def valuation_buffett(file, ticket):
    
    arquivo = file
    df = pd.read_csv(arquivo, sep=';', encoding='utf-8', index_col=0)
    
    df = limpar_numeros(df)
    # =========================
    # 1. LIMPEZA DOS DADOS
    # =========================
    # df = df.drop(columns=["2025"], errors="ignore")
    # df = df.drop(columns=["2024"], errors="ignore")
    # df = df.apply(pd.to_numeric, errors="coerce")

    # =========================
    # 2. DIVIDENDOS
    # =========================
    # Assumindo colunas do mais recente → mais antigo
    cols_3y = df.columns[:3]
    cols_5y = df.columns[:5]

    # Dividendo médio (3 anos) → D0
    div_medio_3y = df.loc["Div", cols_3y].mean()

    # CAGR dos dividendos (5 anos)
    div_inicio = df.loc["Div", cols_5y[-1]]
    div_fim = df.loc["Div", cols_5y[0]]

    if div_inicio > 0:
        cagr_div_5y = (div_fim / div_inicio) ** (1 / 5) - 1
    else:
        cagr_div_5y = 0

    # Cap conservador de crescimento (Buffett)
    g = min(max(cagr_div_5y, 0), 0.06)

    # =========================
    # 3. PARÂMETROS
    # =========================
    KE = 0.12  # custo de capital conservador

    # =========================
    # 4. VALUATION (DDM)
    # =========================
    def dividend_discount_model(div, g, ke):
        if ke <= g:
            return np.nan
        div_futuro = div * (1 + g)
        return div_futuro / (ke - g)

    valor_intrinseco = dividend_discount_model(
        div=div_medio_3y,
        g=g,
        ke=KE
    )

    tabela_valor_intrinseco = pd.DataFrame(
        {"Valor Intrínseco (R$)": [valor_intrinseco]},
        index=["Base"]
    )

    preco_max_compra = valor_intrinseco * 0.7

    tabela_margem = pd.DataFrame({
        "Valor Intrínseco": [valor_intrinseco],
        "Margem de Segurança (30%)": [valor_intrinseco * 0.3],
        "Preço Máximo de Compra": [preco_max_compra]
    })
    
    return tabela_valor_intrinseco

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
    preco_inicio = cotation(ticket, 2026) #2026
    preco_fim = cotation(ticket, 2026) #2027
    valor_intrinceco = valuation_buffett(f"{file}{ticket}.csv", ticket).iloc[0,0]
    
    results = {
        "ticket": ticket.upper(),
        "valor_intrinseco": valor_intrinceco.round(2),
        "desconto": ((preco_inicio - valor_intrinceco)/valor_intrinceco).round(4) * 100,
        "preco_inicio": preco_inicio.round(2),
        "preco_fim": preco_fim.round(2),
        "variacao_percentual": ((preco_fim - preco_inicio)/preco_inicio).round(4) * 100
    }
    
    return results