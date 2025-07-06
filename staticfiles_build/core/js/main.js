// Archivo: core/static/core/js/main.js (VERSIÓN FINAL PARA RESOLVER M3U8)
document.addEventListener('DOMContentLoaded', function() {

    // --- 1. Lógica del Menú Hamburguesa ---
    const hamburgerMenu = document.getElementById('hamburger-menu');
    const navbarContent = document.getElementById('navbar-right-content');
    if (hamburgerMenu && navbarContent) {
        hamburgerMenu.addEventListener('click', () => {
            hamburgerMenu.classList.toggle('open');
            navbarContent.classList.toggle('open');
        });
    }

    // --- 2. Barra de Navegación Interactiva ---
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
    
    // =======================================================
    // === 3. LÓGICA DEL REPRODUCTOR (REESCRITA PARA LA API) ===
    // =======================================================
    function setupPlayer(containerSelector) {
        const container = document.querySelector(containerSelector);
        if (!container) return; 

        const videoElement = document.getElementById('player');
        const playerMessageOverlay = document.getElementById('player-message-overlay');
        const playerMessageText = document.getElementById('player-message-text');

        if (!videoElement || !playerMessageOverlay || !playerMessageText) {
            console.error("Faltan elementos del reproductor en el HTML.");
            return;
        }

        const player = new Plyr(videoElement);
        const hls = new Hls();

        function showMessage(text) {
            player.stop();
            hls.detachMedia();
            videoElement.style.display = 'none';
            playerMessageOverlay.style.display = 'flex';
            playerMessageText.textContent = text;
        }
        
        function showPlayer() {
            playerMessageOverlay.style.display = 'none';
            videoElement.style.display = 'block';
        }

        function handleButtonClick(button) {
            const serverName = button.dataset.serverName;
            const sourceId = button.dataset.sourceId;

            if (!serverName || !sourceId) {
                showMessage('Error: Botón sin datos.');
                return;
            }

            document.querySelectorAll('.source-button').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            showMessage(`Resolviendo ${serverName}...`);
            
            const apiUrl = `/api/resolve/${serverName}/${sourceId}/`;

            fetch(apiUrl)
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => { throw new Error(err.error || `Error ${response.status}`) });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success && data.m3u8_url) {
                        showPlayer();
                        if (Hls.isSupported()) {
                            hls.loadSource(data.m3u8_url);
                            hls.attachMedia(videoElement);
                        } else {
                            videoElement.src = data.m3u8_url;
                        }
                    } else {
                        throw new Error(data.error || 'Fallo al obtener la URL.');
                    }
                })
                .catch(error => {
                    console.error('Error al cargar la fuente:', error);
                    showMessage(error.message);
                });
        }

        // Event listener para los clics manuales del usuario
        container.addEventListener('click', function(event) {
            const button = event.target.closest('.source-button');
            if (button) {
                handleButtonClick(button);
            }
        });

        // Carga automática del primer botón disponible
        const firstButton = container.querySelector('.source-button');
        if (firstButton) {
            console.log("Iniciando carga automática del primer servidor...");
            handleButtonClick(firstButton); 
        } else {
            showMessage("No hay fuentes de vídeo disponibles.");
        }
    }

    // Ejecutamos la función para ambas páginas (películas y episodios)
    setupPlayer('.movie-sources');
    setupPlayer('.episode-sources');


    // --- 4. Lógica para Series en la página de detalle ---
    const seasonsContainer = document.querySelector('.seasons-container');
    const episodesContainer = document.querySelector('.episodes-container');

    if (seasonsContainer && episodesContainer) {
        const seasonButtons = seasonsContainer.querySelectorAll('.season-button');
        
        seasonButtons.forEach(button => {
            button.addEventListener('click', function() {
                seasonButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                const seasonNumber = this.getAttribute('data-season');
                const allEpisodeLists = episodesContainer.querySelectorAll('.episodes-list');
                allEpisodeLists.forEach(list => list.classList.remove('active'));
                const activeEpisodeList = episodesContainer.querySelector(`.episodes-list[data-season="${seasonNumber}"]`);
                if (activeEpisodeList) {
                    activeEpisodeList.classList.add('active');
                }
            });
        });

        if (seasonButtons.length > 0) {
            seasonButtons[0].click();
        }
    }

    // --- 5. LÓGICA PARA CARGAR MÁS CONTENIDO ---
    const loadMoreBtn = document.getElementById('load-more-btn');
    const contentGrid = document.getElementById('content-grid');
    const loadingSpinner = document.getElementById('loading-spinner');

    function createContentCard(item) {
        const itemType = item.type || 'Película'; 
        let detailUrl;
        if (item.type === 'Película') {
            detailUrl = `/pelicula/${item.id}/`;
        } else if (item.type === 'Serie') {
            detailUrl = `/serie/${item.id}/`;
        } else { // Anime
            detailUrl = `/anime/${item.id}/`;
        }
        let imageHtml = `<div class="no-poster"><span>${item.title}</span></div>`;
        if (item.poster_path) {
            const imageUrl = item.poster_path.startsWith('http')
                ? item.poster_path
                : `https://image.tmdb.org/t/p/w500${item.poster_path}`;
            imageHtml = `<img src="${imageUrl}" alt="${item.title}" loading="lazy" class="card-image">`;
        }
        return `
            <a href="${detailUrl}" class="content-card" data-title="${item.title}">
                ${imageHtml}
                <div class="card-overlay">
                    <h3 class="card-title">${item.title}</h3>
                    <span class="card-type">${itemType}</span>
                </div>
            </a>
        `;
    }

    if (loadMoreBtn && contentGrid) {
        loadMoreBtn.addEventListener('click', function() {
            let page = this.getAttribute('data-page');
            const type = this.getAttribute('data-type');
            
            loadMoreBtn.style.display = 'none';
            if (loadingSpinner) loadingSpinner.style.display = 'block';

            const url = `/cargar-mas/?page=${page}&type=${type}`;
            
            fetch(url)
                .then(response => {
                    if (!response.ok) { throw new Error(`Error del servidor: ${response.status} ${response.statusText}`); }
                    return response.json();
                })
                .then(data => {
                    if (data.items && data.items.length > 0) {
                        const allCardsHTML = data.items.map(item => createContentCard(item)).join('');
                        contentGrid.insertAdjacentHTML('beforeend', allCardsHTML);
                    }
                    if (data.has_more) {
                        this.setAttribute('data-page', parseInt(page) + 1);
                        loadMoreBtn.style.display = 'inline-block';
                    } else {
                        this.remove();
                    }
                })
                .catch(error => { console.error('Error en fetch:', error); loadMoreBtn.style.display = 'inline-block'; })
                .finally(() => { if (loadingSpinner) loadingSpinner.style.display = 'none'; });
        });
    }

    // --- 6. LÓGICA PARA MENÚS DESPLEGABLES (ACORDEÓN) ---
    function setupDropdowns(containerSelector) {
        const container = document.querySelector(containerSelector);
        if (!container) return;

        container.addEventListener('click', (event) => {
            const clickedSummary = event.target.closest('.dropdown-summary');

            if (event.target.matches('.source-button')) {
                const parentDetails = event.target.closest('.dropdown-menu');
                if (parentDetails) { parentDetails.open = false; }
                return;
            }

            if (clickedSummary) {
                const parentDetails = clickedSummary.closest('.dropdown-menu');
                container.querySelectorAll('.dropdown-menu').forEach(details => {
                    if (details !== parentDetails) {
                        details.open = false;
                    }
                });
            }
        });
    }

    setupDropdowns('.movie-sources');
    setupDropdowns('.episode-sources');
});