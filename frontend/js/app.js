/**
 * App.js — Dashboard logic for CineMatch
 * Handles trending movies, search, recommendations, and poster loading.
 */

const API_BASE = window.location.origin;
const TOKEN = localStorage.getItem('token');
const USERNAME = localStorage.getItem('username');

// ─── Poster Cache ───
const posterCache = {};

// ─── Auth Guard ───
if (!TOKEN) {
    window.location.href = '/';
}

// ─── Toast ───
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ─── API Helper ───
async function apiFetch(url) {
    const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${TOKEN}` },
    });
    if (res.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.href = '/';
        return null;
    }
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Request failed');
    }
    return res.json();
}

// ─── Init ───
function init() {
    // Set user info
    document.getElementById('userAvatar').textContent = USERNAME ? USERNAME[0].toUpperCase() : 'U';
    document.getElementById('usernameDisplay').textContent = USERNAME || 'User';
    document.getElementById('heroUsername').textContent = USERNAME || 'User';

    // Load trending
    loadTrending();

    // Search
    const searchInput = document.getElementById('searchInput');
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        const q = searchInput.value.trim();
        if (q.length < 2) {
            hideSearchResults();
            return;
        }
        searchTimeout = setTimeout(() => searchMovies(q), 400);
    });

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', () => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.href = '/';
    });

    // Modal close
    document.getElementById('closeModalBtn').addEventListener('click', closeModal);
    document.getElementById('recommendModal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closeModal();
    });

    // Load more
    document.getElementById('loadMoreBtn').addEventListener('click', () => {
        currentPage++;
        loadTrending(true);
    });
}

// ─── Trending ───
let currentPage = 1;

async function loadTrending(append = false) {
    const grid = document.getElementById('trendingGrid');
    if (!append) {
        grid.innerHTML = `<div class="loading-spinner" style="grid-column:1/-1"><div class="spinner"></div><span class="loading-text">Loading trending movies...</span></div>`;
    }

    try {
        const data = await apiFetch(`${API_BASE}/api/movies/trending?page=${currentPage}&per_page=20`);
        if (!data) return;

        if (!append) grid.innerHTML = '';

        data.movies.forEach(movie => {
            grid.appendChild(createMovieCard(movie));
        });

        // Load posters asynchronously
        loadPostersForGrid(grid);
    } catch (err) {
        grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="icon">😕</div><h3>Failed to load movies</h3><p>${err.message}</p></div>`;
    }
}

// ─── Search ───
async function searchMovies(query) {
    const section = document.getElementById('searchResultsSection');
    const grid = document.getElementById('searchResultsGrid');
    const label = document.getElementById('searchQueryLabel');

    section.classList.add('active');
    label.textContent = query;
    grid.innerHTML = `<div class="loading-spinner" style="grid-column:1/-1"><div class="spinner"></div><span class="loading-text">Searching...</span></div>`;

    try {
        const data = await apiFetch(`${API_BASE}/api/movies/search?q=${encodeURIComponent(query)}`);
        if (!data) return;

        grid.innerHTML = '';
        if (data.movies.length === 0) {
            grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="icon">🔍</div><h3>No movies found</h3><p>Try a different search term</p></div>`;
            return;
        }

        data.movies.forEach(movie => {
            grid.appendChild(createMovieCard(movie));
        });

        loadPostersForGrid(grid);
    } catch (err) {
        grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="icon">😕</div><h3>Search failed</h3><p>${err.message}</p></div>`;
    }
}

function hideSearchResults() {
    document.getElementById('searchResultsSection').classList.remove('active');
}

// ─── Recommendations ───
async function getRecommendations(title) {
    const modal = document.getElementById('recommendModal');
    const container = document.getElementById('recommendationsContainer');
    const sourceTitle = document.getElementById('modalSourceTitle');

    sourceTitle.textContent = title;
    container.innerHTML = `<div class="loading-spinner"><div class="spinner"></div><span class="loading-text">Finding similar movies...</span></div>`;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    try {
        const data = await apiFetch(`${API_BASE}/api/movies/recommend/${encodeURIComponent(title)}`);
        if (!data) return;

        container.innerHTML = '';
        const grid = document.createElement('div');
        grid.className = 'rec-grid';

        data.recommendations.forEach(movie => {
            grid.appendChild(createMovieCard(movie, true));
        });

        container.appendChild(grid);
        loadPostersForGrid(grid);
    } catch (err) {
        container.innerHTML = `<div class="empty-state"><div class="icon">😕</div><h3>No recommendations found</h3><p>${err.message}</p></div>`;
    }
}

function closeModal() {
    document.getElementById('recommendModal').classList.remove('active');
    document.body.style.overflow = '';
}

// ─── Movie Card Builder ───
function createMovieCard(movie, isRec = false) {
    const card = document.createElement('div');
    card.className = 'movie-card';
    card.dataset.title = movie.title;

    // Parse first genre
    let genreDisplay = '';
    if (movie.genres) {
        const genres = movie.genres.replace(/[\[\]']/g, '').split(',');
        genreDisplay = genres[0] ? genres[0].trim() : '';
    }

    const rating = movie.vote_average ? movie.vote_average.toFixed(1) : '—';

    card.innerHTML = `
        <div class="poster-placeholder">
            <div class="icon">🎬</div>
            <div class="p-title">${escapeHtml(movie.title)}</div>
        </div>
        <div class="movie-overlay">
            <div class="movie-title">${escapeHtml(movie.title)}</div>
            <div class="movie-meta">
                <span class="rating-badge">⭐ ${rating}</span>
                ${genreDisplay ? `<span class="genre-tag">${escapeHtml(genreDisplay)}</span>` : ''}
            </div>
        </div>
        <div class="movie-actions">
            <button class="btn-recommend" onclick="event.stopPropagation(); getRecommendations('${escapeJs(movie.title)}')">
                ✨ Similar Movies
            </button>
        </div>
    `;

    card.addEventListener('click', () => {
        getRecommendations(movie.title);
    });

    return card;
}

// ─── Poster Loading (client-side TMDB → CSS background-image) ───
const TMDB_KEY = 'b068fc68792e0fad2bbe6c5a2cfefa80';

function loadPostersForGrid(grid) {
    const cards = grid.querySelectorAll('.movie-card');
    cards.forEach(card => {
        const title = card.dataset.title;
        if (!title) return;
        if (posterCache[title]) {
            applyPosterBg(card, posterCache[title]);
            return;
        }
        fetch(`https://api.themoviedb.org/3/search/movie?api_key=${TMDB_KEY}&query=${encodeURIComponent(title)}`)
            .then(r => r.json())
            .then(data => {
                if (data.results && data.results.length > 0 && data.results[0].poster_path) {
                    const url = 'https://image.tmdb.org/t/p/w500' + data.results[0].poster_path;
                    posterCache[title] = url;
                    applyPosterBg(card, url);
                }
            })
            .catch(e => console.warn('Poster fetch error:', title, e));
    });
}

function applyPosterBg(card, url) {
    const placeholder = card.querySelector('.poster-placeholder');
    if (!placeholder) return;
    // Pre-load image, then apply as background
    const testImg = new Image();
    testImg.onload = () => {
        placeholder.style.backgroundImage = `url(${url})`;
        placeholder.style.backgroundSize = 'cover';
        placeholder.style.backgroundPosition = 'center';
        // Hide the text/icon content
        placeholder.querySelectorAll('.icon, .p-title').forEach(el => el.style.display = 'none');
    };
    testImg.onerror = () => console.warn('Image load failed:', url);
    testImg.src = url;
}

// ─── Utility ───
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}

function escapeJs(str) {
    return (str || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

// ─── Keyboard shortcuts ───
document.addEventListener('keydown', (e) => {
    // Escape closes modal
    if (e.key === 'Escape') closeModal();
    // Ctrl+K focuses search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('searchInput').focus();
    }
});

// ─── Start ───
init();
