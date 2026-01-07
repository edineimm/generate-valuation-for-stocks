import webbrowser
import pyautogui
import time
import os

def open_website_for_ticket(site, ticket):
    
    if site.lower() == "statusinvest":
        URL = f"https://statusinvest.com.br/acoes/{ticket}"
        
    elif site.lower() == "dividendos":
        URL = f"https://www.dadosdemercado.com.br/acoes/{ticket}/dividendos"
        
    # =====================================
    # 1. FECHAR A ABA ATUAL
    # =====================================
    # CTRL + W fecha a aba
    pyautogui.hotkey('ctrl', 'w')

    time.sleep(1)

    # =====================================
    # 2. ABRIR O CHROME NA URL DEFINIDA
    # =====================================
    webbrowser.open(URL)

    # aguarda o Chrome abrir e carregar a página
    time.sleep(6)
