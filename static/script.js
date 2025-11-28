document.addEventListener('DOMContentLoaded', () => {
    const gamesGrid = document.getElementById('games-grid');
    
    // ⚠️ ALTERAÇÃO: Aponta para a porta padrão do Flask (5000)
    const BACKEND_URL = 'http://localhost:5000/api/games';

    async function fetchNBAGames(dateIso = null) { 
        let gamesToday = []; 
        let standingsData = [];
        gamesGrid.innerHTML = '<p style="text-align: center;">Carregando jogos...</p>';
        
        try {
            // Monta a URL: se a data for passada em ISO (YYYY-MM-DD), envia como query
            let url = BACKEND_URL;
            if (dateIso) {
                // encode a data para query
                url = `${BACKEND_URL}?date=${encodeURIComponent(dateIso)}`;
            }

            // A requisição agora vai para o seu servidor Python/Flask
            const response = await fetch(url);
            
            if (!response.ok) {
                 throw new Error(`Erro de rede ou no servidor! Status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // A resposta do backend retorna 'data' (games) e opcionalmente 'standings'.
            gamesToday = data.data || [];
            standingsData = data.standings || [];
            
        } catch (error) {
            console.error('Erro ao buscar jogos:', error);
            gamesGrid.innerHTML = `
                <p style="color: red; text-align: center;">Falha ao carregar os jogos. Verifique se o backend está rodando em ${BACKEND_URL}</p>
            `;
            // Em caso de erro, continuará e exibirá mensagem na tela
        }
        
        displayGames(gamesToday);
        displayStandings(standingsData);
    }

    function getField(obj, names) {
        for (const n of names) {
            if (obj[n] !== undefined && obj[n] !== null) return obj[n];
        }
        return null;
    }

    function displayGames(games) {
        const gamesGrid = document.getElementById('games-grid');
        gamesGrid.innerHTML = ''; 
        
        // Verifica se a API retornou dados
        if (!games || games.length === 0) {
            gamesGrid.innerHTML = '<p style="text-align: center; color: #666;">Nenhum jogo encontrado para a data selecionada.</p>';
            return;
        }

        games.forEach(game => {
            // Tentamos localizar vários nomes de campo que podem vir do backend
            const homeTeamName = getField(game, ['HOME_TEAM_NAME', 'home_team_name', 'HOME_TEAM_ABBREVIATION', 'HOME_TEAM_ABBREV']) || 'Casa';
            const visitorTeamName = getField(game, ['VISITOR_TEAM_NAME', 'visitor_team_name', 'VISITOR_TEAM_ABBREVIATION', 'VISITOR_TEAM_ABBREV']) || 'Visitante';
            const gameStatus = getField(game, ['GAME_STATUS_TEXT', 'game_status_text', 'STATUS']) || '';

            // Placar (usa 0 se o placar for nulo)
            const homeScore = getField(game, ['PTS_HOME', 'HOME_PTS', 'home_team_score', 'home_score']) || 0;
            const visitorScore = getField(game, ['PTS_AWAY', 'AWAY_PTS', 'visitor_team_score', 'away_score']) || 0;

            // Determina se o jogo acabou
            const isFinal = gameStatus && String(gameStatus).toLowerCase().includes('final');
            
            // Monta a linha de placar/confronto
            const score = isFinal 
                ? `${visitorTeamName} ${visitorScore} @ ${homeTeamName} ${homeScore}`
                : `${visitorTeamName} @ ${homeTeamName}`;
                
            // Status de exibição
            const statusDisplay = isFinal ? `FINAL` : gameStatus;
            
            // O campo da data se chama GAME_DATE_EST e precisa ser formatado:
            const rawDate = getField(game, ['GAME_DATE_EST', 'game_date_est', 'GAME_DATE']) || null;
            let gameDate = '';
            if (rawDate) {
                try { gameDate = new Date(rawDate).toLocaleDateString('pt-BR'); } catch (e) { gameDate = rawDate; }
            }

            const gameCard = document.createElement('div');
            gameCard.classList.add('game-card');
            gameCard.innerHTML = `
                <div class="team-names">${score}</div>
                <div class="game-details">Status: <strong>${statusDisplay}</strong></div>
                <div class="game-details">Data: ${gameDate}</div>
            `;
            gamesGrid.appendChild(gameCard);
        });
    }

        function displayStandings(standings) {
            const container = document.getElementById('standings-container');
            container.innerHTML = '';

            if (!standings || standings.length === 0) {
                container.innerHTML = '<p style="text-align:center;">Nenhuma tabela de standings disponível.</p>';
                return;
            }

            // Cria tabela simples
            const table = document.createElement('table');
            table.style.width = '100%';
            table.style.borderCollapse = 'collapse';

            // Cabeçalho
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            ['Posição','Time','Vitórias','Derrotas','%Vit'].forEach(h => {
                const th = document.createElement('th');
                th.innerText = h;
                th.style.border = '1px solid #ddd';
                th.style.padding = '8px';
                th.style.textAlign = 'left';
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);

            const tbody = document.createElement('tbody');

            standings.forEach((s, idx) => {
                const row = document.createElement('tr');
                    const teamName = getField(s, ['TeamName','TEAM_NAME','team_name','TEAM','teamFullName','TeamCity']) || 'Time';
                    const wins = getField(s, ['W','WINS','wins','Wins']) || getField(s, ['TEAM_WINS','team_wins']) || 0;
                    const losses = getField(s, ['L','LOSSES','losses','Losses']) || getField(s, ['TEAM_LOSSES','team_losses']) || 0;
                    const pct = getField(s, ['WinPCT','WIN_PCT','PCT','win_pct']) || getField(s,['WinPCT','WinPCT']) || '';

                [idx+1, teamName, wins, losses, pct].forEach(val => {
                    const td = document.createElement('td');
                    td.innerText = val;
                    td.style.border = '1px solid #ddd';
                    td.style.padding = '8px';
                    row.appendChild(td);
                });

                tbody.appendChild(row);
            });

            table.appendChild(tbody);
            container.appendChild(table);
        }

    // Define handlers do seletor de data
    const datePicker = document.getElementById('date-picker');
    const fetchBtn = document.getElementById('fetch-date-btn');
    const todayBtn = document.getElementById('today-btn');

    // Ao clicar em buscar, usa o valor do input (formato YYYY-MM-DD)
    fetchBtn.addEventListener('click', () => {
        const v = datePicker.value; // '' ou 'YYYY-MM-DD'
        if (!v) {
            alert('Selecione uma data primeiro.');
            return;
        }
        fetchNBAGames(v);
    });

    // Botão hoje: limpa o input e busca hoje
    todayBtn.addEventListener('click', () => {
        datePicker.value = '';
        fetchNBAGames();
    });

    // Busca inicial: hoje
    fetchNBAGames();
});