from datetime import datetime
import pandas as pd
import math
import numpy as np
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
# Endpoints para jogos: ScoreboardV2 (próximos/atuais) e LeagueGameFinder (histórico com placares)
from nba_api.stats.endpoints import ScoreboardV2, LeagueGameFinder

# Tentativa de importar diferentes endpoints de standings, conforme disponibilidade
StandingsEndpoint = None
for candidate in ('StandingsV3', 'LeagueStandings', 'LeagueStandingsV3', 'Standings'):
    try:
        module = __import__('nba_api.stats.endpoints', fromlist=[candidate])
        StandingsEndpoint = getattr(module, candidate)
        print(f"DEBUG: usando endpoint de standings: {candidate}")
        break
    except Exception:
        StandingsEndpoint = None

# Inicializa o Flask
app = Flask(__name__) 
CORS(app) 

# --- ROTA RAIZ (Serve o index.html) ---
@app.route('/')
def index():
    # Renderiza o arquivo HTML que contém o frontend
    return render_template('index.html')


# --- ROTA DE TESTE ---
@app.route('/api/test', methods=['GET'])
def test():
    """Endpoint simples para testar conectividade."""
    return jsonify({'status': 'ok', 'message': 'Backend is running'})


# --- ROTA PRINCIPAL: /api/games (Usando NBA API) ---
@app.route('/api/games', methods=['GET'])
def get_nba_games():
    """Busca jogos da NBA para a data atual usando nba_api."""
    
    try:
        # 1. Permite passar data via querystring (?date=YYYY-MM-DD ou MM/DD/YYYY)
        query_date = None
        try:
            query_date = request.args.get('date')
        except Exception:
            query_date = None

        if query_date:
            # aceita formatos ISO (YYYY-MM-DD) ou MM/DD/YYYY
            try:
                if '-' in query_date:
                    # YYYY-MM-DD -> converte para MM/DD/YYYY
                    parsed = datetime.fromisoformat(query_date)
                    today_date = parsed.strftime('%m/%d/%Y')
                    query_date_iso = parsed.strftime('%m/%d/%Y')
                else:
                    # assume já MM/DD/YYYY
                    datetime.strptime(query_date, '%m/%d/%Y')
                    today_date = query_date
                    query_date_iso = query_date
            except Exception:
                # fallback para hoje se parsing falhar
                today_date = datetime.now().strftime('%m/%d/%Y')
                query_date_iso = today_date
        else:
            # default: hoje
            today_date = datetime.now().strftime('%m/%d/%Y')
            query_date_iso = today_date

        # 2. Tenta primeiro buscar com LeagueGameFinder (tem placares para jogos finalizados)
        games_list = []
        try:
            finder = LeagueGameFinder(date_from_nullable=query_date_iso, date_to_nullable=query_date_iso)
            games_df = finder.get_data_frames()[0]
            
            if len(games_df) > 0:
                # LeagueGameFinder retorna 1 linha por time (2 linhas por jogo)
                # Agrupa e combina em um dicionário por GAME_ID
                games_by_id = {}
                for _, row in games_df.iterrows():
                    game_id = row['GAME_ID']
                    matchup = row['MATCHUP']  # ex: "BOS vs. DET" ou "DET @ BOS"
                    team_id = row['TEAM_ID']
                    team_name = row['TEAM_NAME']
                    team_abbrev = row.get('TEAM_ABBREVIATION', '')
                    pts = int(row['PTS'])
                    
                    if game_id not in games_by_id:
                        games_by_id[game_id] = {
                            'GAME_ID': game_id,
                            'GAME_DATE_EST': row['GAME_DATE'],
                            'MATCHUP': matchup,
                            'GAME_STATUS_ID': 2,  # LeagueGameFinder sempre retorna jogos finalizados
                            'GAME_STATUS_TEXT': 'Final',
                            'PTS_HOME': None,
                            'PTS_AWAY': None,
                            'HOME_TEAM_ID': None,
                            'VISITOR_TEAM_ID': None,
                            'HOME_TEAM_NAME': None,
                            'VISITOR_TEAM_NAME': None,
                            'HOME_TEAM_ABBREV': None,
                            'VISITOR_TEAM_ABBREV': None,
                        }
                    
                    # Identifica se é home ou away baseado no MATCHUP
                    # Ex: "DET @ BOS" -> DET é visitante (@), BOS é home
                    # Ex: "BOS vs. DET" -> BOS é home (vs), DET é visitante
                    if ' @ ' in matchup:
                        # Time antes do @ é visitante, time depois é home
                        parts = matchup.split(' @ ')
                        if team_abbrev == parts[0].strip():
                            # É visitante
                            games_by_id[game_id]['VISITOR_TEAM_ID'] = team_id
                            games_by_id[game_id]['VISITOR_TEAM_NAME'] = team_name
                            games_by_id[game_id]['VISITOR_TEAM_ABBREV'] = team_abbrev
                            games_by_id[game_id]['PTS_AWAY'] = pts
                        else:
                            # É home
                            games_by_id[game_id]['HOME_TEAM_ID'] = team_id
                            games_by_id[game_id]['HOME_TEAM_NAME'] = team_name
                            games_by_id[game_id]['HOME_TEAM_ABBREV'] = team_abbrev
                            games_by_id[game_id]['PTS_HOME'] = pts
                    else:
                        # TEAM vs. OPPONENT - team before "vs" é home
                        parts = matchup.split(' vs')
                        if team_abbrev == parts[0].strip():
                            # É home
                            games_by_id[game_id]['HOME_TEAM_ID'] = team_id
                            games_by_id[game_id]['HOME_TEAM_NAME'] = team_name
                            games_by_id[game_id]['HOME_TEAM_ABBREV'] = team_abbrev
                            games_by_id[game_id]['PTS_HOME'] = pts
                        else:
                            # É visitante
                            games_by_id[game_id]['VISITOR_TEAM_ID'] = team_id
                            games_by_id[game_id]['VISITOR_TEAM_NAME'] = team_name
                            games_by_id[game_id]['VISITOR_TEAM_ABBREV'] = team_abbrev
                            games_by_id[game_id]['PTS_AWAY'] = pts
                
                games_list = list(games_by_id.values())
        
        except Exception as e:
            print(f"INFO: LeagueGameFinder não encontrou jogos para {query_date_iso}, tentando ScoreboardV2: {e}")
        
        # 3. Se LeagueGameFinder não retornar resultados, usa ScoreboardV2 (para jogos futuros)
        if len(games_list) == 0:
            schedule = ScoreboardV2(game_date=today_date)
            games_df = schedule.get_data_frames()[0]
            games_list = games_df.to_dict('records')

            # Enriquece os jogos com o nome do time (mapeia IDs para nomes)
            try:
                from nba_api.stats.static import teams as nba_teams
                teams_list = nba_teams.get_teams()
                team_map = {t['id']: t.get('full_name') for t in teams_list}
                team_abbrev = {t['id']: t.get('abbreviation') for t in teams_list}
                for g in games_list:
                    hid = g.get('HOME_TEAM_ID')
                    vid = g.get('VISITOR_TEAM_ID')
                    if hid in team_map:
                        g['HOME_TEAM_NAME'] = team_map[hid]
                        g['HOME_TEAM_ABBREV'] = team_abbrev.get(hid)
                    if vid in team_map:
                        g['VISITOR_TEAM_NAME'] = team_map[vid]
                        g['VISITOR_TEAM_ABBREV'] = team_abbrev.get(vid)
            except Exception as e:
                print(f"WARN: não foi possível mapear nomes dos times: {e}")
        else:
            # Se usou LeagueGameFinder, tenta enriquecer com abreviaturas também
            try:
                from nba_api.stats.static import teams as nba_teams
                teams_list = nba_teams.get_teams()
                team_abbrev = {t['id']: t.get('abbreviation') for t in teams_list}
                for g in games_list:
                    hid = g.get('HOME_TEAM_ID')
                    vid = g.get('VISITOR_TEAM_ID')
                    if hid in team_abbrev:
                        g['HOME_TEAM_ABBREV'] = team_abbrev.get(hid)
                    if vid in team_abbrev:
                        g['VISITOR_TEAM_ABBREV'] = team_abbrev.get(vid)
            except Exception as e:
                print(f"WARN: não foi possível mapear abreviaturas dos times: {e}")
        
        # 4. Busca a tabela de standings (tenta vários endpoints disponíveis)
        standings_list = []
        if StandingsEndpoint is not None:
            try:
                standings = StandingsEndpoint()
                dfs = standings.get_data_frames()
                if dfs and len(dfs) > 0:
                    standings_df = dfs[0]
                    standings_list = standings_df.to_dict('records')
            except Exception as e:
                print(f"WARN: falha ao obter standings com {StandingsEndpoint}: {e}")

        # Sanitiza valores que não são JSON-serializáveis (NaN, numpy types, datetimes)
        def sanitize_value(v):
            # pandas NA, numpy nan
            try:
                if pd.isna(v):
                    return None
            except Exception:
                pass

            # numpy scalar types
            if isinstance(v, (np.integer,)):
                return int(v)
            if isinstance(v, (np.floating,)):
                # convert NaN/inf to None
                if math.isnan(float(v)) or math.isinf(float(v)):
                    return None
                return float(v)

            # python floats (check NaN/inf)
            if isinstance(v, float):
                if math.isnan(v) or math.isinf(v):
                    return None
                return v

            # datetime -> ISO string
            if isinstance(v, datetime):
                return v.isoformat()

            # bytes -> decode
            if isinstance(v, (bytes, bytearray)):
                try:
                    return v.decode('utf-8')
                except Exception:
                    return str(v)

            # fallback: leave basic types as-is, otherwise convert to str
            if isinstance(v, (str, bool, int)):
                return v
            return str(v)

        def sanitize_obj(o):
            if isinstance(o, dict):
                return {k: sanitize_obj(v) for k, v in o.items()}
            if isinstance(o, list):
                return [sanitize_obj(x) for x in o]
            return sanitize_value(o)

        # Logs de depuração: quantos jogos/standings foram retornados e amostra das chaves
        try:
            print(f"DEBUG: games found: {len(games_list)}")
            if len(games_list) > 0:
                sample = games_list[0]
                print("DEBUG: sample game keys:", list(sample.keys()))
            print(f"DEBUG: standings found: {len(standings_list)}")
            if len(standings_list) > 0:
                print("DEBUG: sample standing keys:", list(standings_list[0].keys()))
        except Exception:
            pass

        # Aplica sanitização antes de serializar para JSON
        try:
            games_list = sanitize_obj(games_list)
            standings_list = sanitize_obj(standings_list)
        except Exception:
            pass

        # 5. Retorna os dados no formato esperado pelo frontend
        return jsonify({'data': games_list, 'standings': standings_list})
        
    except Exception as e:
        print(f"ERRO CRÍTICO ao buscar dados da NBA API: {e}")
        # Em caso de falha de rede ou API, retorna um erro controlado
        return jsonify({
            'message': 'Falha ao buscar dados dos Jogos (Erro de API ou Conexão).',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)