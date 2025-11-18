
import os
from datetime import datetime
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
# ⚠️ Configuração CORS: Permite que seu frontend se conecte
CORS(app) 

# --- Configuração da Chave de API Balldontlie ---
BALDONTLIE_API_KEY = os.getenv("BALDONTLIE_API_KEY")
BASE_URL = 'https://nba.balldontlie.io/v2' 

if not BALDONTLIE_API_KEY:
    print("ERRO: A variável de ambiente BALDONTLIE_API_KEY não está definida.")
    exit(1)

# ----------------------------------------------------
# ROTA PRINCIPAL: /api/games
# ----------------------------------------------------
@app.route('/api/games', methods=['GET'])
def get_nba_games():
    """Busca jogos da NBA para a data atual."""
    
    # 1. Determina a data de hoje no formato YYYY-MM-DD para o filtro
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 2. Constrói a URL para a API Balldontlie com o filtro de data
    # (Se precisar de paginação ou outros filtros, você pode adicionar 'request.args')
    api_url = f"{BASE_URL}/games?dates[]={today}"
    
    print(f"Buscando jogos em: {api_url}")
    
    try:
        # Faz a requisição HTTP para a Balldontlie API
        response = requests.get(
            api_url,
            headers={
                # Sua chave de API segura no servidor
                'Authorization': BALDONTLIE_API_KEY,
                'Content-Type': 'application/json'
            }
        )
        
        # Levanta um erro se o status for 4xx ou 5xx
        response.raise_for_status()
        
        # Retorna os dados da Balldontlie diretamente para o seu frontend
        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados da Balldontlie: {e}")
        # Retorna um erro amigável para o frontend
        return jsonify({
            'message': 'Falha ao buscar dados dos Jogos da API Balldontlie.',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    # Roda o servidor Flask na porta 5000 (padrão do Flask)
    app.run(debug=True, port=5000)