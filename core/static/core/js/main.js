// Archivo: core/static/core/js/main.js (VERSIÓN FINAL PARA ENLACES PRE-PROCESADOS)

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM cargado. Iniciando main.js para enlaces pre-procesados...");

    // =======================================================
    // === 1. LÓGICA DE LA INTERFAZ PRINCIPAL (NAVBAR, MENÚ)
    // =======================================================
    const hamburgerMenu = document.getElementById('hamburger-menu');
    const navbarContent = document.getElementById('navbar-right-content');
    if (hamburgerMenu && navbarContent) {
        hamburgerMenu.addEventListener('click', () => {
            hamburgerMenu.classList.toggle('open');
            navbarContent.classList.toggle('open');
        });
    }

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
    // === 2. LÓGICA UNIFICADA DEL REPRODUCTOR Y MENÚS
    // =======================================================
    
    const playerAndOptions = document.querySelector('.player-and-options');

    if (playerAndOptions) {
        console.log("Reproductor detectado. Iniciando lógica de resolución dinámica...");

        const videoElement = document.getElementById('player');
        const playerMessageOverlay = document.getElementById('player-message-overlay');
        const playerMessageText = document.getElementById('player-message-text');

        if (!videoElement || !playerMessageOverlay || !playerMessageText) {
            console.error("Error crítico: Faltan elementos del reproductor en el HTML.");
            return;
        }

        const player = new Plyr(videoElement);
        let hls = new Hls();

        function showMessage(text, isError = false) {
            console.log(`Mostrando mensaje en overlay: "${text}"`);
            player.stop();
            if (hls && hls.media) hls.detachMedia();
            videoElement.style.display = 'none';
            playerMessageOverlay.style.display = 'flex';
            playerMessageText.textContent = text;
            playerMessageText.style.color = isError ? '#ff4d4d' : '#e0e0e0';
        }

        async function handleSourceButtonClick(button) {
            const serverName = button.dataset.serverName;
            const sourceId = button.dataset.sourceId;

            if (!serverName || !sourceId) {
                showMessage(`Error: El botón no tiene los datos necesarios.`, true);
                return;
            }

            document.querySelectorAll('.source-button').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            showMessage(`Resolviendo ${serverName}...`);

            try {
                // Aquí está la magia: llamamos a nuestra API de Django
                const apiUrl = `/api/v1/resolve/${serverName}/${sourceId}/`;
                console.log(`Fetching: ${apiUrl}`);
                
                const response = await fetch(apiUrl);

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `Error del servidor: ${response.status}`);
                }

                const data = await response.json();

                if (data.success && data.url) {
                    console.log("¡Éxito! M3U8 recibido:", data.url);
                    playerMessageOverlay.style.display = 'none';
                    videoElement.style.display = 'block';

                    if (Hls.isSupported()) {
                        hls.loadSource(data.url);
                        hls.attachMedia(videoElement);
                    } else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
                        videoElement.src = data.url;
                    } else {
                        showMessage("Tu navegador no soporta streaming HLS.", true);
                    }
                } else {
                    throw new Error(data.error || "La API no devolvió una URL válida.");
                }
            } catch (error) {
                console.error("Error al resolver la fuente:", error);
                showMessage(`Fallo al cargar ${serverName}: ${error.message}`, true);
            }
        }

        // GESTOR DE EVENTOS CENTRALIZADO (se mantiene similar)
        playerAndOptions.addEventListener('click', function(event) {
            const sourceButton = event.target.closest('.source-button:not(.season-button)');
            if (sourceButton) {
                handleSourceButtonClick(sourceButton);
                const parentDetails = sourceButton.closest('.dropdown-menu');
                if (parentDetails) parentDetails.open = false;
            }
            // ... (tu lógica para cerrar otros menús desplegables se queda igual) ...
        });

        // CARGA AUTOMÁTICA DEL PRIMER BOTÓN (se mantiene igual)
        const firstSourceButton = playerAndOptions.querySelector('.source-button:not(.season-button)');
        if (firstSourceButton) {
            console.log("Iniciando carga automática del primer servidor...");
            handleSourceButtonClick(firstSourceButton);
        } else {
            showMessage("No hay fuentes de vídeo disponibles.", true);
        }
    } else {
        console.log("No se detectó ningún reproductor en esta página.");
    }
    
    // =======================================================
    // === 3. LÓGICA PARA SERIES EN LA PÁGINA DE DETALLE
    // =======================================================
    const seasonsContainer = document.querySelector('.seasons-container');
    if (seasonsContainer) {
        seasonsContainer.addEventListener('click', function(event){
            const button = event.target.closest('.season-button');
            if(button){
                document.querySelectorAll('.season-button').forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                const seasonNumber = button.dataset.season;
                document.querySelectorAll('.episodes-list').forEach(list => list.classList.remove('active'));
                
                const activeList = document.querySelector(`.episodes-list[data-season="${seasonNumber}"]`);
                if(activeList) activeList.classList.add('active');
            }
        });

        const firstSeasonButton = seasonsContainer.querySelector('.season-button');
        if (firstSeasonButton) {
            firstSeasonButton.click();
        }
    }

    // =======================================================
    // === 4. LÓGICA PARA CARGAR MÁS CONTENIDO
    // =======================================================
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