import os
from datetime import datetime
import requests
from requests.exceptions import JSONDecodeError, RequestException
from flask import Flask, jsonify, render_template 
from flask_cors import CORS
from dotenv import dotenv_values


app = Flask(__name__) 
CORS(app) 

# ✅ NOVO TRECHO DE LEITURA (MAIS ROBUSTO)
# ⚠️ Certifique-se de que o nome da variável no seu .env seja 'BALLDONTLIE_API_KEY'

# Carrega o arquivo .env diretamente para um dicionário
config = dotenv_values(".env")

# Acessa a chave diretamente do dicionário de configuração
BALLDONTLIE_API_KEY = config.get("BALLDONTLIE_API_KEY")
BASE_URL = 'https://nba.balldontlie.io/v2' 

if not BALLDONTLIE_API_KEY:
    print("ERRO: A variável de ambiente BALLDONTLIE_API_KEY não está definida. Verifique o arquivo .env.")
    exit(1)

# ROTA 1: Rota Raiz (/)
@app.route('/')
def index():
    return render_template('index.html')


# ROTA 2: API Proxy (/api/games)
@app.route('/api/games', methods=['GET'])
def get_nba_games():
    datetime.now().strftime('%Y-%m-%d')
    api_url = f"{BASE_URL}/games?dates[]={today}"
    
    try:
        response = requests.get(
            api_url,
            headers={
                'Authorization': BALLDONTLIE_API_KEY, 
                'Content-Type': 'application/json'
            }
        )
        
        response.raise_for_status() 
        
        # ⚠️ TRATAMENTO DE ERRO CRÍTICO (Corrige o 'AttributeError' e o 'JSONDecodeError')
        try:
            return jsonify(response.json())
        except JSONDecodeError:
            # Não acessamos response.status diretamente aqui para evitar o novo erro
            print(f"AVISO: A API retornou Status OK (200), mas sem dados JSON válidos (Sem jogos hoje?). Retornando lista vazia.")
            return jsonify({'data': []}), 200 
            
    except RequestException as e:
        print(f"ERRO DE REQUISIÇÃO: {e}")
        return jsonify({
            'message': 'Falha ao buscar dados dos Jogos. (Verifique a API Key)',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)