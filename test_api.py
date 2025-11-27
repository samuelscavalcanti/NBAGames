# test_api.py
import os
import requests
from dotenv import load_dotenv

# Carrega as variáveis do .env (verifica se o arquivo está sendo lido)
load_dotenv()

# Usa o mesmo nome de variável do seu app.py
BALLDONTLIE_API_KEY = os.getenv("BALLDONTLIE_API_KEY") 
BASE_URL = 'https://nba.balldontlie.io/v2'

if not BALLDONTLIE_API_KEY:
    print("ERRO: O ARQUIVO .env NÃO ESTÁ SENDO LIDO. Verifique o nome (.env) e a localização (raiz do projeto).")
    exit()

print("STATUS: Chave lida com sucesso. Tentando conectar à API...")

try:
    response = requests.get(
        f"{BASE_URL}/teams",  # Ponto de acesso simples
        headers={
            'Authorization': BALLDONTLIE_API_KEY,
            'Content-Type': 'application/json'
        }
    )
    
    # Levanta erro para status 4xx ou 5xx
    response.raise_for_status()

    # Se chegou aqui, a chave está OK!
    print("✅ SUCESSO! A CHAVE DE API É VÁLIDA E FUNCIONOU.")
    # Verifica o conteúdo (apenas o primeiro time)
    data = response.json()
    print(f"Dados recebidos com sucesso. Primeiro time: {data['data'][0]['full_name']}")

except requests.exceptions.HTTPError as e:
    # Captura erros comuns como 401 (Não autorizado), 403 (Proibido)
    print(f"❌ FALHA DE AUTORIZAÇÃO: A CHAVE DE API FOI REJEITADA.")
    print(f"STATUS CODE: {e.response.status_code}")
    print("SOLUÇÃO: Verifique sua chave no arquivo .env (se ela expirou ou foi digitada incorretamente).")
    
except Exception as e:
    print(f"ERRO INESPERADO: Falha ao conectar/decodificar. Detalhes: {e}")