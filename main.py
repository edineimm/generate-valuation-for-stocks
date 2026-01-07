import idiv
import web_scraping
import open_website
import valuation_unit
import valuation_for_roe
import pandas as pd
import time
import logging
import os

logging.basicConfig(level=logging.INFO)

Folder = "IBOV"
PATH= f"C:\\Users\\edine\\OneDrive\\Documentos\\stocks\\B3\\{Folder}\\"
PATH_File = f"C:\\Users\\edine\\OneDrive\\Documentos\\stocks\\b3\\indices\\{Folder.lower()} b3.csv"
results = []

# obtem a lista de tickers do idiv
tickers = idiv.get_ticker(PATH_File)

def obtem_balanco(tickers):
    for i in tickers:
        inicio = time.perf_counter()
        
        print(f"\n=== PROCESSANDO TICKER: {i} ===")
        
        if os.path.exists(f'{PATH}{i}.csv'):
            print(f"Arquivo {i}.csv já existe. Pulando...")
            continue
        else:
            # obtem os indicadores financeiros
            indicators = web_scraping.obtain_financial_indicators(i)

        # obtem os dividendos e preenche o dataframe  
        
        if indicators is None or indicators.empty:
            print(f"Nenhum indicador financeiro encontrado para o ticker {i}. Pulando...")
            continue
        else:
            url = f"https://www.dadosdemercado.com.br/acoes/{i}/dividendos"
            indicators = web_scraping.get_dividends(indicators, url)

            indicators.to_csv(f'{PATH}{i}.csv', sep=';', encoding='utf-8')
        
        # calcula o valor justo e o desconto
        # valuation = valuation_unit.return_ticket(PATH, i)
        # results.append(valuation)
        
        tempo = time.perf_counter() - inicio
        logging.info("Ticker %s executado em %.3fs", i, tempo)

    
def valuation(tickers):
    for i in tickers:
        inicio = time.perf_counter()
        
        # print(f"=== VALUATION TICKER: {i} ===")
        
        # calcula o valor justo e o desconto
        valuation = valuation_unit.return_ticket(PATH, i)
        # valuation = valuation_for_roe.return_ticket(PATH, i)
        results.append(valuation)
        
        tempo = time.perf_counter() - inicio
        logging.info("Valuation Ticker %s executado em %.3fs", i, tempo)
            
    # print("\n=== RESULTADOS CONSOLIDADOS ===")
    df = pd.DataFrame(results)
    # print(df)
    df.to_csv(f'{PATH}resultado_idiv.csv', sep=';', encoding='utf-8')
    
def graficos():
    df = pd.read_csv(f'{PATH}resultado_idiv.csv', sep=';', encoding='utf-8')
    df = df[(df["desconto"] < - 30) & (df["desconto"] > -50)].sort_values(by='desconto', ascending=True)
    # print(df[["ticket", "valor_intrinseco", "desconto"]])
    tickets = []
    tickets = df["ticket"].tolist()
    # print(tickets)
    # valuation(tickers)

    df_setores = pd.read_csv(
        f'{PATH}setores.csv',
        sep=';',
        encoding='utf-8')
    
    df["ticket"] = df["ticket"].str.upper()
    df_setores["Ticket"] = df_setores["Ticket"].str.upper()
    
    df_final = df.merge(
    df_setores,
    left_on="ticket",
    right_on="Ticket",
    how="left"
    )
    
    df = df_final[['ticket', 'valor_intrinseco', 'desconto', 'preco_inicio',
       'preco_fim', 'variacao_percentual',
       'Subsetor de Atuação', 'Segmento de Atuação']]
    
    df = df.sort_values(
    by=["Segmento de Atuação", "desconto"],
    ascending=[True, True]
    )
    
    print(df)

def get_setor(tickers):
    results = []

    for i in tickers:
        df_setor = web_scraping.setor(i)  # JÁ É UM DATAFRAME
        results.append(df_setor)
        print(df_setor)

    df = pd.concat(results, ignore_index=True)

    df.to_csv(
        f'{PATH}setores.csv',
        sep=';',
        encoding='utf-8',
        index=False
    )

    return df
# obtem_balanco(tickers)
valuation(tickers)
# get_setor(tickers)
graficos()