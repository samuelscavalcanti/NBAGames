# app.py (AJUSTADO para servir o index.html)

import os
from datetime import datetime
import requests
from flask import Flask, jsonify, request, render_template # <-- Importar render_template
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ... (Configurações de app, CORS, API Key) ...

# ----------------------------------------------------
# ROTA DE SERVIÇO: Renderiza o HTML
# ----------------------------------------------------
@app.route('/')
def index():
    # Flask procura automaticamente o arquivo em 'templates/index.html'
    return render_template('index.html')

# ----------------------------------------------------
# ROTA DA API: /api/games (Seu proxy)
# ----------------------------------------------------
@app.route('/api/games', methods=['GET'])
def get_nba_games():
    # ... (Seu código existente para buscar a API Balldontlie) ...
    # (Não precisa de alteração neste bloco)
    today = datetime.now().strftime('%Y-%m-%d')
    api_url = f"{BASE_URL}/games?dates[]={today}"
    # ...
    try:
        response = requests.get(
            api_url,
            headers={'Authorization': BALDONTLIE_API_KEY, 'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'message': 'Falha ao buscar dados dos Jogos.'}), 500

if __name__ == '__main__':
    # O servidor Flask será a porta de entrada da sua aplicação
    app.run(debug=True, port=5000)