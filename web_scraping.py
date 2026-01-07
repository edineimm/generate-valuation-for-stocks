import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

def get_html_statusinvest(ticker, max_tentativas=3):

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    # driver.get(f"https://statusinvest.com.br/acoes/{ticker}")
    driver.get(f"https://statusinvest.com.br/acoes/eua/{ticker}")
    print("Página StatusInvest carregada.")

    for tentativa in range(1, max_tentativas + 1):
        try:
            print(f"Tentativa {tentativa} de clicar no HISTÓRICO")

            btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@title='Histórico do ativo']"))
            )

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(0.5)

            # clique via JS é mais confiável em SPAs
            driver.execute_script("arguments[0].click();", btn)

            # aguarda a tabela aparecer
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.table-history"))
            )

            print("Tabela histórica carregada.")
            break  # sucesso → sai do loop

        except TimeoutException:
            print("Tabela ainda não apareceu, tentando novamente...")
            time.sleep(1)

    else:
        print("Falha ao carregar histórico após várias tentativas.")
        driver.quit()
        return None

    html = driver.page_source
    driver.quit()
    return html


def extract_table_history(html):
    soup = BeautifulSoup(html, "html.parser")

    # localizar todas as tabelas históricas
    tables = soup.select("div.table-history")
    dfs = []

    for t_index, table_div in enumerate(tables, start=1):
        # capturar cabeçalhos (anos)
        headers = [th.get_text(strip=True) for th in table_div.select("div.tr div.th")]
        if not headers:
            continue

        # capturar linhas de valores
        rows = table_div.select("div.tr.asset-last")

        data = []
        for idx, row in enumerate(rows):
            valores = [td.get_text(strip=True) for td in row.select("div.td")]
            registro = dict(zip(headers, valores))
            registro["Indicador"] = f"Tabela{t_index}_Linha{idx+1}"
            data.append(registro)

        df = pd.DataFrame(data)
        df.set_index("Indicador", inplace=True)
        dfs.append(df)

    # concatenar todas as tabelas encontradas
    if dfs:
        return pd.concat(dfs)
    else:
        return pd.DataFrame()
    

def obtain_financial_indicators(ticket):
    
    html = get_html_statusinvest(ticket)
    if html is None:
        return None

    # ======================================================
    # 3. Extrair os dados
    # ======================================================
    df_historico = extract_table_history(html)

    # cria uma linha vazia com as mesmas colunas
    linha_vazia = pd.DataFrame(
        [[np.nan] * len(df_historico.columns)],
        columns=df_historico.columns
    )

    # concatena: primeira linha | linha vazia | resto
    df = pd.concat(
        [df_historico.iloc[:1], linha_vazia, df_historico.iloc[1:]],
        ignore_index=True
    )

    # ======================================================
    # 4. Ajustar índice com nomes dos indicadores
    # ======================================================
    indicadores = [
        'D.Y', 'Div', 'P/L', 'PEG Ratio', 'P/VP', 'EV/EBITDA', 'EV/EBIT',
        'P/EBITDA', 'P/EBIT', 'VPA', 'P/Ativo', 'LPA', 'P/SR', 'P/Cap. Giro',
        'P/Ativo Circ. Liq.', 'Dív. líquida/PL', 'Dív. líquida/EBITDA',
        'Dív. líquida/EBIT', 'PL/Ativos', 'Passivos/Ativos', 'Liq. corrente',
        'M. Bruta', 'M. EBITDA', 'M. EBIT', 'M. Líquida', 'ROE', 'ROA', 'ROIC',
        'Giro ativos', 'CAGR Receitas 5 anos', 'CAGR Lucros 5 anos'
    ]
    df.index = indicadores

    # remover coluna "ATUAL" se existir
    df.drop(columns=["ATUAL"], inplace=True, errors='ignore')
    
    return df

# ======================================================
# 1. Obter HTML da página
# ======================================================
def get_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


# ======================================================
# 2. Encontrar a tabela de dividendos (robusto)
# ======================================================
def find_dividend_table(soup):
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if {"Ano", "Dividendos", "DY"}.issubset(headers):
            return table
    return None


# ======================================================
# 3. Extrair tabela genérica
# ======================================================
def extract_table(table):
    headers = [th.get_text(strip=True) for th in table.find_all("th")]

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        rows.append(
            [td.get_text(strip=True) for td in tr.find_all("td")]
        )

    return pd.DataFrame(rows, columns=headers)


# ======================================================
# 4. Função principal – preenche df_fundamentos
# ======================================================
def get_dividends(df_fundamentos, url):
    print(f"Acessando a pagina de dividendos")
    html = get_html(url)
    soup = BeautifulSoup(html, "html.parser")

    table = find_dividend_table(soup)
    if table is None:
        raise ValueError("Tabela de dividendos não encontrada")

    df_div = extract_table(table)

    # =========================
    # Limpeza dos dados
    # =========================
    df_div["Ano"] = df_div["Ano"].astype(str)

    df_div["Dividendos"] = (
        df_div["Dividendos"]
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    # =========================
    # Preencher df_fundamentos
    # =========================
    serie_div = df_div.set_index("Ano")["Dividendos"]

    anos_comuns = df_fundamentos.columns.intersection(serie_div.index)
    df_fundamentos.loc["Div", anos_comuns] = serie_div.loc[anos_comuns]

    return df_fundamentos

from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_setor_html_statusinvest(ticker, max_tentativas=3):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(f"https://statusinvest.com.br/acoes/{ticker}")

        # Aguarda o carregamento do bloco de informações de setor
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[contains(text(), 'Setor de Atuação')]")
            )
        )

        print("Elemento 'Setor de Atuação' carregado.")

        html = driver.page_source
        return html

    finally:
        driver.quit()

def setor(ticket):
    html = get_setor_html_statusinvest(ticket)

    soup = BeautifulSoup(html, "html.parser")

    data = {
        "Ticket": ticket.upper(),
        "Setor de Atuação": None,
        "Subsetor de Atuação": None,
        "Segmento de Atuação": None
    }

    for info in soup.select("div.info"):
        label_tag = info.select_one("span.sub-value")
        value_tag = info.select_one("strong.value")

        if label_tag and value_tag:
            label = label_tag.get_text(strip=True)
            value = value_tag.get_text(strip=True)
            data[label] = value

    df = pd.DataFrame([data])
    df = df[["Ticket", "Setor de Atuação", "Subsetor de Atuação", "Segmento de Atuação"]]
    return df