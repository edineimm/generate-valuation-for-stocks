import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

arquivo = r"C:\Users\edine\OneDrive\Documentos\stocks\b3\setor\bancario\bancario_consolidado.csv"
df = pd.read_csv(arquivo, sep=';', encoding='utf-8', index_col=0)

tickets = df['ticket'].unique().tolist()
print(tickets)

def cotation_delta(ticket, start_date, end_date):
    ticker = yf.Ticker(f"{ticket}.SA")
    
    dados = ticker.history(
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=True
    )

    if dados.empty:
        raise ValueError(f"Sem dados para o ativo {ticket}")

    dados.index = dados.index.tz_localize(None)  # <<< AQUI

    return dados[['Close']].copy().rename(columns={'Close': ticket})


def cotation_index(symbol, start_date, end_date):
    dados = yf.download(
        symbol,
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if dados.empty:
        raise ValueError(f"Sem dados para o índice {symbol}")

    dados.index = dados.index.tz_localize(None)  # <<< AQUI

    return dados[['Close']].copy().rename(columns={'Close': symbol})


# =========================
# PERÍODO
# =========================
start_date = '2025-01-01'
end_date = '2025-12-31'

# =========================
# ATIVOS
# =========================
tickets = [t.replace('.SA', '') for t in tickets]

dfs = []

# Ações
for ativo in tickets:
    dfs.append(cotation_delta(ativo, start_date, end_date))

# IVVB11
dfs.append(cotation_delta('IVVB11', start_date, end_date))

# IBOVESPA
dfs.append(cotation_index('^BVSP', start_date, end_date))

# =========================
# DATAFRAME FINAL
# =========================
df_precos = pd.concat(dfs, axis=1)

# remove datas incompletas
df_precos.dropna(inplace=True)

# normaliza base 100
df_precos = (df_precos / df_precos.iloc[0]) * 100

plt.figure(figsize=(14, 7))
df_precos.plot(ax=plt.gca(), linewidth=2)

plt.title('Performance Comparativa – Base 100', fontsize=14)
plt.ylabel('Base 100')
plt.xlabel('Data')
plt.grid(alpha=0.3)
plt.legend(title='Ativos')

plt.tight_layout()
plt.show()
