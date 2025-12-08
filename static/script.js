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
            const homeScore = getField(game, ['PTS_HOME', 'HOME_PTS', 'home_team_score', 'home_score']);
            const visitorScore = getField(game, ['PTS_AWAY', 'AWAY_PTS', 'visitor_team_score', 'away_score']);

            // Determina se o jogo tem placar (jogo já foi disputado)
            const hasScore = homeScore !== null && homeScore !== undefined && visitorScore !== null && visitorScore !== undefined;
            
            // Determina se o jogo foi finalizado (status Final ou tem placar)
            const isFinal = hasScore || (gameStatus && String(gameStatus).toLowerCase().includes('final'));
            
            // Monta a linha de placar/confronto - exibe placar para jogos com score
            let score;
            if (hasScore) {
                score = `${visitorTeamName} ${visitorScore} @ ${homeTeamName} ${homeScore}`;
            } else {
                score = `${visitorTeamName} @ ${homeTeamName}`;
            }
                
            // Status de exibição
            const statusDisplay = isFinal ? `FINAL` : gameStatus;
            
            // O campo da data se chama GAME_DATE_EST e precisa ser formatado.
            // Quando a API retorna apenas 'YYYY-MM-DD' o construtor Date interpreta como UTC,
            // o que causa um deslocamento de dia em fusos-horários negativos. Para evitar isso,
            // parseamos manualmente YYYY-MM-DD como data LOCAL.
            const rawDate = getField(game, ['GAME_DATE_EST', 'game_date_est', 'GAME_DATE']) || null;
            let gameDate = '';
            if (rawDate) {
                // Formato esperado: 2025-11-26
                const ymd = /^([0-9]{4})-([0-9]{2})-([0-9]{2})$/.exec(String(rawDate));
                if (ymd) {
                    const year = Number(ymd[1]);
                    const month = Number(ymd[2]) - 1; // monthIndex
                    const day = Number(ymd[3]);
                    try {
                        // cria a data no fuso local (midnight local)
                        const d = new Date(year, month, day);
                        gameDate = d.toLocaleDateString('pt-BR');
                    } catch (e) {
                        gameDate = rawDate;
                    }
                } else {
                    try {
                        gameDate = new Date(rawDate).toLocaleDateString('pt-BR');
                    } catch (e) {
                        gameDate = rawDate;
                    }
                }
            }

            const gameCard = document.createElement('div');
            gameCard.classList.add('game-card');
            // Destaca visualmente jogos finalizados
            if (isFinal) {
                gameCard.style.borderLeft = '4px solid #28a745';
            }
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

            // Agrupa times por conferência
            const east = [];
            const west = [];

            standings.forEach(s => {
                const conference = getField(s, ['Conference', 'CONFERENCE', 'conference']) || '';
                if (conference.toLowerCase().includes('east')) {
                    east.push(s);
                } else if (conference.toLowerCase().includes('west')) {
                    west.push(s);
                }
            });

            // Função para criar tabela de uma conferência
            const createConferenceTable = (teams, conferenceName) => {
                const section = document.createElement('div');
                section.style.marginBottom = '32px';

                const title = document.createElement('h3');
                title.innerText = `Conferência ${conferenceName}`;
                title.style.textAlign = 'center';
                title.style.marginBottom = '12px';
                section.appendChild(title);

                const table = document.createElement('table');
                table.style.width = '100%';
                table.style.borderCollapse = 'collapse';

                // Cabeçalho
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                headerRow.style.backgroundColor = '#f0f0f0';
                ['Posição','Time','Vitórias','Derrotas','%Vit'].forEach(h => {
                    const th = document.createElement('th');
                    th.innerText = h;
                    th.style.border = '1px solid #ddd';
                    th.style.padding = '8px';
                    th.style.textAlign = 'left';
                    th.style.fontWeight = 'bold';
                    headerRow.appendChild(th);
                });
                thead.appendChild(headerRow);
                table.appendChild(thead);

                const tbody = document.createElement('tbody');

                teams.forEach((s, idx) => {
                    const row = document.createElement('tr');
                    if (idx % 2 === 0) {
                        row.style.backgroundColor = '#f9f9f9';
                    }
                    
                    const teamName = getField(s, ['TeamName','TEAM_NAME','team_name','TEAM','teamFullName','TeamCity']) || 'Time';
                    const wins = getField(s, ['W','WINS','wins','Wins']) || getField(s, ['TEAM_WINS','team_wins']) || 0;
                    const losses = getField(s, ['L','LOSSES','losses','Losses']) || getField(s, ['TEAM_LOSSES','team_losses']) || 0;
                    const pct = getField(s, ['WinPCT','WIN_PCT','PCT','win_pct']) || '';

                    // Formata porcentagem
                    let pctDisplay = '';
                    if (pct) {
                        if (typeof pct === 'number') {
                            pctDisplay = (pct * 100).toFixed(1) + '%';
                        } else {
                            pctDisplay = String(pct);
                        }
                    }

                    [idx+1, teamName, wins, losses, pctDisplay].forEach(val => {
                        const td = document.createElement('td');
                        td.innerText = val;
                        td.style.border = '1px solid #ddd';
                        td.style.padding = '8px';
                        row.appendChild(td);
                    });

                    tbody.appendChild(row);
                });

                table.appendChild(tbody);
                section.appendChild(table);
                return section;
            };

            // Adiciona tabelas de ambas as conferências
            if (east.length > 0) {
                container.appendChild(createConferenceTable(east, 'Leste'));
            }
            if (west.length > 0) {
                container.appendChild(createConferenceTable(west, 'Oeste'));
            }
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