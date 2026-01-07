import pandas as pd
import numpy as np
import yfinance as yf

arquivo = r"C:\Users\edine\OneDrive\Documentos\stocks\b3\setor\bancario\bancario_consolidado.csv"
df = pd.read_csv(arquivo, sep=';', encoding='utf-8', index_col=0)

tickets = df['ticket'].unique().tolist()
print(tickets)

def valuation_buffett(df, ticket):
    # =========================
    # 1. LIMPEZA DOS DADOS
    # =========================
    df = df.drop(columns=["ticket"], errors="ignore")
    df = df.apply(pd.to_numeric, errors="coerce")

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

    # =========================
    # 5. OUTPUT
    # =========================
    # print(f"\n=== VALUATION BUFFETT | {ticket} ===")
    # print(f"Dividendo médio (3y): R$ {div_medio_3y:.2f}")
    # print(f"CAGR Div (5y): {cagr_div_5y:.2%}")
    # print(f"Crescimento usado (g): {g:.2%}")
    # print(f"Custo de capital (KE): {KE:.2%}")

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

    # print("\n=== VALOR INTRÍNSECO ===")
    # print(tabela_valor_intrinseco.round(2))

    # print("\n=== MARGEM DE SEGURANÇA ===")
    # print(tabela_margem.round(2))

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

results = []

for ticket in tickets:
    df_ticket = df[df['ticket'] == ticket]
    print(f"Analisando o ticket: {ticket.upper()}")
    preco_inicio = cotation(ticket, 2025)
    preco_fim = cotation(ticket, 2026)
    valor_intrinceco = valuation_buffett(df[df['ticket'] == ticket], ticket).iloc[0,0]
    
    results.append({
        "ticket": ticket.upper(),
        "valor_intrinseco": valor_intrinceco.round(2),
        "desconto": ((preco_inicio - valor_intrinceco)/valor_intrinceco).round(4) * 100,
        "preco_inicio": preco_inicio.round(2),
        "preco_fim": preco_fim.round(2),
        "variacao_percentual": ((preco_fim - preco_inicio)/preco_inicio).round(4) * 100
    })
                   
    
print("\n=== RESULTADOS CONSOLIDADOS ===")
results_df = pd.DataFrame(results)
print(results_df.sort_values(by="desconto", ascending=True).round(2))