/**
 * Home Page Logic
 */

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initialize Quick Search Form
  const searchForm = document.getElementById('home-search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const location = document.getElementById('search-location').value.trim();
      const sport = document.getElementById('search-sport').value.trim();
      const date = document.getElementById('search-date').value;

      const params = new URLSearchParams();
      if (location) params.append('location', location);
      if (sport) params.append('sport', sport);
      if (date) params.append('date', date);

      window.location.href = `/turfs?${params.toString()}`;
    });
  }

  // Set min date on date picker to today
  const dateInput = document.getElementById('search-date');
  if (dateInput) {
    const todayStr = new Date().toISOString().split('T')[0];
    dateInput.min = todayStr;
    dateInput.value = todayStr;
  }

  // 2. Fetch & Render Featured Turfs from Real Backend
  const featuredContainer = document.getElementById('featured-turfs-container');
  if (featuredContainer) {
    try {
      const res = await API.get('/turfs', { sort: 'rating_desc' });
      if (res.ok && res.data && res.data.turfs) {
        const turfs = res.data.turfs.slice(0, 3);
        if (turfs.length === 0) {
          featuredContainer.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
              <div class="empty-state-icon">🏟️</div>
              <div class="empty-state-title">No Turfs Available</div>
              <div class="empty-state-text">Check back soon as new facilities are added daily!</div>
            </div>
          `;
          return;
        }

        featuredContainer.innerHTML = turfs.map(turf => `
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
                ⚡ ${turf.facilities.slice(0, 4).join(' • ')}
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
      }
    } catch (err) {
      console.error('Failed to load featured turfs:', err);
      featuredContainer.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-title">Unable to Load Turfs</div>
          <div class="empty-state-text">Please refresh the page to retry.</div>
        </div>
      `;
    }
  }
});
