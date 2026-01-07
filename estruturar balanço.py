import pandas as pd
import re
import os
import glob

def strutured_data(ticket):
    # Nome do arquivo txt de entrada
    arquivo_txt = ticket

    # Ler todo o conteúdo do arquivo
    with open(arquivo_txt, "r", encoding="utf-8") as f:
        raw_data = f.read()

    # Separar por categorias
    categorias = re.split(r'Indicadores de ', raw_data)[1:]  
    todos_indicadores = []
    todos_valores = []
    anos_globais = []

    for categoria_raw in categorias:
        linhas = [l.strip() for l in categoria_raw.split('\n') if l.strip()]

        # Captura indicadores
        indicadores = []
        i = 1
        while i < len(linhas) and not linhas[i].startswith("ATUAL"):
            if linhas[i] not in ['format_quote', 'help_outline', 'show_chart']:
                indicadores.append(linhas[i])
            i += 1

        # Captura anos
        anos = []
        if i < len(linhas) and linhas[i].startswith("ATUAL"):
            anos = ['ATUAL']
            i += 1
            while i < len(linhas) and re.match(r'\d{4}', linhas[i]):
                anos.append(int(linhas[i]))
                i += 1

        # Guardar anos globais (só uma vez)
        if not anos_globais:
            anos_globais = anos

        n_anos = len(anos)

        # Captura valores
        for indicador in indicadores:
            valores = []
            while len(valores) < n_anos and i < len(linhas):
                linha = linhas[i].replace('%', '').strip()
                if linha in ['-', '']:
                    valores.append(None)
                else:
                    try:
                        valores.append(float(linha.replace(',', '.')))
                    except:
                        valores.append(None)
                i += 1
            todos_indicadores.append(indicador)
            todos_valores.append(valores)

    # Criar DataFrame único
    df_consolidado = pd.DataFrame(todos_valores, index=todos_indicadores, columns=anos_globais)
    match = re.search(r'([^\\]+)(?=\.txt$)', ticket)
    df_consolidado.insert(1, "ticket", match.group(1))
    df_consolidado.to_csv(f'C:\\Users\\edine\\OneDrive\\Documentos\\stocks\\b3\\setor\\bancario\\{match.group(1)}.csv', sep=';', encoding='utf-8')

def obter_arquivos_txt(diretorio):
    if not os.path.isdir(diretorio):
        raise ValueError(f"Diretório não encontrado: {diretorio}")
    
    # Usa glob para encontrar todos os .txt
    arquivos_txt = glob.glob(os.path.join(diretorio, "*.txt"))
    return arquivos_txt

if __name__ == "__main__":
    
    diretorio = "C:\\Users\\edine\\OneDrive\\Documentos\\stocks\\b3\\setor\\bancario\\balanços"
    arquivos = obter_arquivos_txt(diretorio)
    for arq in arquivos:
        strutured_data(arq) 