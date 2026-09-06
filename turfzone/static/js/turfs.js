/**
 * Turf Discovery & Marketplace Logic
 */

let debounceTimer = null;

async function loadTurfs() {
  const container = document.getElementById('turfs-grid-container');
  const countBadge = document.getElementById('turf-count-badge');
  if (!container) return;

  container.innerHTML = '<div class="spinner" style="grid-column: 1 / -1;"></div>';

  const search = document.getElementById('filter-search')?.value.trim() || '';
  const sport = document.getElementById('filter-sport')?.value || '';
  const location = document.getElementById('filter-location')?.value || '';
  const maxPrice = document.getElementById('filter-price')?.value || '';
  const minRating = document.getElementById('filter-rating')?.value || '';
  const sort = document.getElementById('filter-sort')?.value || 'rating_desc';

  const params = {};
  if (search) params.search = search;
  if (sport && sport !== 'all') params.sport = sport;
  if (location && location !== 'all') params.location = location;
  if (maxPrice) params.max_price = maxPrice;
  if (minRating) params.min_rating = minRating;
  if (sort) params.sort = sort;

  const res = await API.get('/turfs', params);

  if (res.ok && res.data) {
    const turfs = res.data.turfs || [];
    if (countBadge) countBadge.textContent = `${turfs.length} Turfs Found`;

    if (turfs.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">🔍</div>
          <div class="empty-state-title">No Turfs Found</div>
          <div class="empty-state-text">No sports facilities matched your filter criteria. Try adjusting your filters or search terms.</div>
          <button onclick="resetFilters()" class="btn btn-outline btn-sm">Reset Filters</button>
        </div>
      `;
      return;
    }

    container.innerHTML = turfs.map(turf => `
      <div class="card turf-card">
        <div class="turf-card-img-wrap">
          <img src="${turf.image_url}" alt="${turf.name}" loading="lazy">
          <div class="turf-card-overlay">
            <span class="badge badge-emerald">⭐ ${turf.rating} (${turf.reviews_count})</span>
            <span class="badge badge-emerald">Available</span>
          </div>
        </div>
        <div class="turf-card-body">
          <h3 class="turf-card-title">${turf.name}</h3>
          <div class="turf-card-loc">
            <span>📍</span>
            <span>${turf.location}</span>
          </div>
          <div class="turf-card-sports">
            ${turf.sport.split(',').map(s => `<span class="badge badge-purple">${s.trim()}</span>`).join('')}
          </div>
          <p class="turf-card-amenities">
            ⚡ ${turf.facilities.slice(0, 3).join(' • ')}
          </p>
          <div class="turf-card-footer">
            <div class="turf-card-price">
              <span class="amount">₹${turf.price_per_hour}</span>
              <span class="unit">per hour</span>
            </div>
            <div style="display: flex; gap: 0.5rem;">
              <a href="/turf/${turf.id}" class="btn btn-secondary btn-sm">Details</a>
              <a href="/turf/${turf.id}" class="btn btn-primary btn-sm">Book Now</a>
            </div>
          </div>
        </div>
      </div>
    `).join('');
  } else {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-state-icon">⚠️</div>
        <div class="empty-state-title">Error Loading Turfs</div>
        <div class="empty-state-text">${res.message || 'Could not connect to database.'}</div>
        <button onclick="loadTurfs()" class="btn btn-primary btn-sm">Retry</button>
      </div>
    `;
  }
}

function resetFilters() {
  const search = document.getElementById('filter-search');
  const sport = document.getElementById('filter-sport');
  const location = document.getElementById('filter-location');
  const price = document.getElementById('filter-price');
  const priceVal = document.getElementById('price-val-display');
  const rating = document.getElementById('filter-rating');
  const sort = document.getElementById('filter-sort');

  if (search) search.value = '';
  if (sport) sport.value = 'all';
  if (location) location.value = 'all';
  if (price) price.value = '2500';
  if (priceVal) priceVal.textContent = '₹2,500';
  if (rating) rating.value = '0';
  if (sort) sort.value = 'rating_desc';

  loadTurfs();
}

document.addEventListener('DOMContentLoaded', () => {
  // Pre-fill from URL params
  const urlParams = new URLSearchParams(window.location.search);
  const searchInput = document.getElementById('filter-search');
  const sportSelect = document.getElementById('filter-sport');
  const locationSelect = document.getElementById('filter-location');
  const priceRange = document.getElementById('filter-price');
  const priceVal = document.getElementById('price-val-display');
  const ratingSelect = document.getElementById('filter-rating');
  const sortSelect = document.getElementById('filter-sort');

  if (urlParams.get('search') && searchInput) searchInput.value = urlParams.get('search');
  if (urlParams.get('sport') && sportSelect) sportSelect.value = urlParams.get('sport');
  if (urlParams.get('location') && locationSelect) locationSelect.value = urlParams.get('location');
  if (urlParams.get('sort') && sortSelect) sortSelect.value = urlParams.get('sort');

  // Event Listeners for Filters
  searchInput?.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadTurfs, 300);
  });

  sportSelect?.addEventListener('change', loadTurfs);
  locationSelect?.addEventListener('change', loadTurfs);
  ratingSelect?.addEventListener('change', loadTurfs);
  sortSelect?.addEventListener('change', loadTurfs);

  priceRange?.addEventListener('input', (e) => {
    if (priceVal) priceVal.textContent = `₹${parseInt(e.target.value).toLocaleString()}`;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadTurfs, 250);
  });

  loadTurfs();
});
