// Archivo: core/static/core/js/main.js (Versión Completa y Robusta)
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
    
    // --- 3. Lógica del Reproductor ---
    const player = document.getElementById('video-player');
    
    function setupPlayer(buttonsContainerSelector) {
        const container = document.querySelector(buttonsContainerSelector);
        if (!container) return;

        const buttons = container.querySelectorAll('.source-button');
        let firstButton = null;

        buttons.forEach(button => {
            if (!firstButton) firstButton = button;
            
            button.addEventListener('click', function() {
                const embedUrl = this.getAttribute('data-embed-url');
                if (player && embedUrl) {
                    player.src = embedUrl;
                }
                buttons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
            });
        });
        
        if (firstButton) {
            firstButton.click();
        } else if (player) {
            player.src = '';
        }
    }
    
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
        // Determina el tipo de contenido. Si no viene, asume Película.
        const itemType = item.type || 'Película'; 

        // Construye la URL de detalle correcta para Película, Serie o Anime.
        let detailUrl;
        if (item.type === 'Película') {
            detailUrl = `/pelicula/${item.id}/`;
        } else if (item.type === 'Serie') {
            detailUrl = `/serie/${item.id}/`;
        } else { // Anime
            detailUrl = `/anime/${item.id}/`;
        }

        // Lógica para el póster. Maneja rutas de TMDB y URLs completas de AniList.
        let imageHtml = `<div class="no-poster"><span>${item.title}</span></div>`;
        if (item.poster_path) {
            const imageUrl = item.poster_path.startsWith('http')
                ? item.poster_path
                : `https://image.tmdb.org/t/p/w500${item.poster_path}`;
            imageHtml = `<img src="${imageUrl}" alt="${item.title}" loading="lazy" class="card-image">`;
        }
        
        // Genera el HTML completo de la tarjeta.
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
                    if (!response.ok) {
                        throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
                    }
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
                .catch(error => {
                    console.error('Error en fetch:', error);
                    loadMoreBtn.style.display = 'inline-block';
                })
                .finally(() => {
                    if (loadingSpinner) loadingSpinner.style.display = 'none';
                });
        });
    }


    // =========================================================================
    // === NUEVA LÓGICA AÑADIDA PARA EL COMPORTAMIENTO DE LOS MENÚS DESPLEGABLES ===
    // =========================================================================

    // Función para cerrar otros menús al abrir uno (comportamiento de acordeón).
    function setupAccordion(containerSelector) {
        const container = document.querySelector(containerSelector);
        if (!container) return;

        const allDetails = container.querySelectorAll('.dropdown-menu');

        allDetails.forEach(details => {
            details.addEventListener('toggle', () => {
                // Si este menú se acaba de abrir...
                if (details.open) {
                    // ...recorremos todos los demás menús.
                    allDetails.forEach(otherDetails => {
                        // Si es un menú diferente al que abrimos y está abierto, lo cerramos.
                        if (otherDetails !== details) {
                            otherDetails.open = false;
                        }
                    });
                }
            });
        });
    }

    // Función para cerrar el menú automáticamente al hacer click en un botón de servidor.
    function setupAutoClose(containerSelector) {
        const container = document.querySelector(containerSelector);
        if (!container) return;

        // Usamos delegación de eventos en el contenedor principal.
        container.addEventListener('click', (event) => {
            // Verificamos si el elemento clickeado es un botón de servidor.
            if (event.target.matches('.source-button')) {
                // Buscamos el elemento <details> padre más cercano.
                const parentDetails = event.target.closest('.dropdown-menu');
                if (parentDetails) {
                    // Cerramos el menú estableciendo su propiedad 'open' a false.
                    parentDetails.open = false;
                }
            }
        });
    }

    // Aplicamos las nuevas funciones a los contenedores de video de películas y episodios.
    setupAccordion('.movie-sources');
    setupAccordion('.episode-sources');
    setupAutoClose('.movie-sources');
    setupAutoClose('.episode-sources');

});