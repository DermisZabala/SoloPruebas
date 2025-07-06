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
        console.log("Reproductor detectado en la página. Configurando...");

        const videoElement = document.getElementById('player');
        const playerMessageOverlay = document.getElementById('player-message-overlay');
        const playerMessageText = document.getElementById('player-message-text');

        if (!videoElement || !playerMessageOverlay || !playerMessageText) {
            console.error("Error crítico: Faltan elementos del reproductor en el HTML.");
        } else {
            const player = new Plyr(videoElement);
            let hls = new Hls();

            function showMessage(text) {
                console.log(`Mostrando mensaje en overlay: "${text}"`);
                player.stop();
                if (hls && hls.media) {
                    hls.detachMedia();
                }
                videoElement.style.display = 'none';
                playerMessageOverlay.style.display = 'flex';
                playerMessageText.textContent = text;
            }

            function handleSourceButtonClick(button) {
                console.log("handleSourceButtonClick activado para:", button);
                const m3u8Url = button.dataset.m3u8Url;
                const serverName = button.dataset.serverName;

                document.querySelectorAll('.source-button').forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');

                // Si la URL del M3U8 existe, la cargamos. Si no, mostramos error.
                if (m3u8Url && m3u8Url !== 'None' && m3u8Url.trim() !== '') {
                    console.log(`URL M3U8 encontrada para ${serverName}: ${m3u8Url}`);
                    
                    // --- Proxy Logic ---
                    // En este modelo, el proxy ya no es estrictamente necesario si los enlaces
                    // resueltos no tienen problemas de CORS. Por ahora lo mantenemos por seguridad.
                    // Si da problemas, la primera prueba es cargar 'm3u8Url' directamente.
                    
                    playerMessageOverlay.style.display = 'none';
                    videoElement.style.display = 'block';
                    
                    if (Hls.isSupported()) {
                        hls.loadSource(m3u8Url); // Cargamos la URL directa
                        hls.attachMedia(videoElement);
                    } else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
                        videoElement.src = m3u8Url; // Cargamos la URL directa
                    } else {
                        showMessage("Tu navegador no soporta streaming HLS.");
                    }
                } else {
                    console.warn(`No se encontró resolved_url para ${serverName}.`);
                    showMessage(`La fuente para ${serverName} no está disponible o el enlace está caído.`);
                }
            }

            // === GESTIÓN DE EVENTOS CENTRALIZADA ===
            playerAndOptions.addEventListener('click', function(event) {
                const sourceButton = event.target.closest('.source-button:not(.season-button)');
                const dropdownSummary = event.target.closest('.dropdown-summary');

                // --- Caso 1: Clic en un botón de fuente ---
                if (sourceButton) {
                    handleSourceButtonClick(sourceButton);
                    const parentDetails = sourceButton.closest('.dropdown-menu');
                    if (parentDetails) {
                        parentDetails.open = false;
                    }
                    return; // Importante para no procesar más clics
                }

                // --- Caso 2: Clic para abrir/cerrar un menú ---
                if (dropdownSummary) {
                    const parentDetails = dropdownSummary.closest('.dropdown-menu');
                    playerAndOptions.querySelectorAll('.dropdown-menu').forEach(details => {
                        if (details !== parentDetails) {
                            details.open = false;
                        }
                    });
                }
            });

            // --- Carga Automática del Primer Botón ---
            const firstSourceButton = playerAndOptions.querySelector('.source-button:not(.season-button)');
            if (firstSourceButton) {
                console.log("Iniciando carga automática del primer servidor...");
                handleSourceButtonClick(firstSourceButton);
            } else {
                showMessage("No hay fuentes de vídeo disponibles.");
                console.warn("No se encontraron botones de fuente para la carga automática.");
            }
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