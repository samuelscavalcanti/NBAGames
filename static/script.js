document.addEventListener('DOMContentLoaded', () => {
    const gamesGrid = document.getElementById('games-grid');
    
    // ⚠️ ALTERAÇÃO: Aponta para a porta padrão do Flask (5000)
    const BACKEND_URL = 'http://localhost:5000/api/games'; 

    async function fetchNBAGames() { 
        let gamesToday = []; 
        gamesGrid.innerHTML = '<p style="text-align: center;">Carregando jogos...</p>';
        
        try {
            // A requisição agora vai para o seu servidor Python/Flask
            const response = await fetch(BACKEND_URL); 
            
            if (!response.ok) {
                 throw new Error(`Erro de rede ou no servidor! Status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // A API Balldontlie retorna os dados de jogos dentro da chave 'data'.
            gamesToday = data.data; 
            
        } catch (error) {
            console.error('Erro ao buscar jogos:', error);
            gamesGrid.innerHTML = `
                <p style="color: red; text-align: center;">Falha ao carregar os jogos. Verifique se o backend está rodando em ${BACKEND_URL}</p>
            `;
            return;
        }
        
        displayGames(gamesToday);
    }

    function displayGames(games) {
        gamesGrid.innerHTML = ''; 
        if (!games || games.length === 0) {
            gamesGrid.innerHTML = '<p style="text-align: center;">Nenhum jogo encontrado para hoje.</p>';
            return;
        }

        games.forEach(game => {
            const homeTeamName = game.home_team.full_name;
            const visitorTeamName = game.visitor_team.full_name;
            
            const score = game.status === 'Final' 
                ? `${visitorTeamName} ${game.visitor_team_score} @ ${homeTeamName} ${game.home_team_score}`
                : `${visitorTeamName} @ ${homeTeamName}`;
                
            const status = game.status === 'Final' ? `FINAL` : game.status;

            const gameCard = document.createElement('div');
            gameCard.classList.add('game-card');
            gameCard.innerHTML = `
                <div class="team-names">${score}</div>
                <div class="game-details">Status: <strong>${status}</strong></div>
                <div class="game-details">Data: ${game.date.substring(0, 10)}</div>
            `;
            gamesGrid.appendChild(gameCard);
        });
    }

    fetchNBAGames();
});