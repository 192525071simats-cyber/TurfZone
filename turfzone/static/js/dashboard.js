/**
 * User Dashboard Logic
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;

  const user = Auth.getUser();

  // Set Greeting
  const greetingElem = document.getElementById('dashboard-user-greeting');
  if (greetingElem) {
    const hours = new Date().getHours();
    let timeOfDay = 'Good morning';
    if (hours >= 12 && hours < 17) timeOfDay = 'Good afternoon';
    else if (hours >= 17) timeOfDay = 'Good evening';
    greetingElem.textContent = `${timeOfDay}, ${user.name}! ⚽`;
  }

  // Load Bookings & Calculate Metrics
  const bookingsRes = await API.get('/bookings');
  if (bookingsRes.ok && bookingsRes.data) {
    const bookings = bookingsRes.data.bookings || [];
    const today = new Date().toISOString().split('T')[0];

    const upcomingBookings = bookings.filter(b => b.status === 'CONFIRMED' && b.booking_date >= today);
    const completedBookings = bookings.filter(b => b.status === 'COMPLETED' || (b.status === 'CONFIRMED' && b.booking_date < today));
    const totalSpent = bookings.filter(b => b.status === 'CONFIRMED' || b.status === 'COMPLETED').reduce((acc, b) => acc + b.price, 0);

    // Update Metric Cards
    const totalBookingsVal = document.getElementById('stat-total-bookings');
    const activeBookingsVal = document.getElementById('stat-active-bookings');
    const completedBookingsVal = document.getElementById('stat-completed-bookings');
    const totalSpentVal = document.getElementById('stat-total-spent');

    if (totalBookingsVal) totalBookingsVal.textContent = bookings.length;
    if (activeBookingsVal) activeBookingsVal.textContent = upcomingBookings.length;
    if (completedBookingsVal) completedBookingsVal.textContent = completedBookings.length;
    if (totalSpentVal) totalSpentVal.textContent = `₹${totalSpent}`;

    // Render Next Upcoming Match Hero Card
    const nextMatchContainer = document.getElementById('next-match-container');
    if (nextMatchContainer) {
      if (upcomingBookings.length > 0) {
        const nextB = upcomingBookings[0];
        nextMatchContainer.innerHTML = `
          <div class="card" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.1)); border: 1px solid rgba(16, 185, 129, 0.3); padding: 1.75rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.25rem;">
              <div>
                <span class="badge badge-emerald" style="margin-bottom: 0.5rem;">🔥 Next Upcoming Match</span>
                <h3 style="font-size: 1.4rem; font-weight: 800; color: var(--text-primary);">${nextB.turf_name}</h3>
                <div style="color: var(--text-secondary); font-size: 0.9rem;">📍 ${nextB.turf_location} • 🏆 ${nextB.sport}</div>
              </div>
              <div style="text-align: right;">
                <div style="font-family: monospace; font-size: 0.95rem; font-weight: 700; color: var(--primary);">${nextB.booking_reference}</div>
                <div class="badge badge-emerald" style="margin-top: 0.3rem;">CONFIRMED</div>
              </div>
            </div>

            <div style="display: flex; gap: 2rem; flex-wrap: wrap; background: rgba(11, 15, 25, 0.6); padding: 1rem 1.25rem; border-radius: var(--radius-md); margin-bottom: 1.25rem;">
              <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Match Date</div>
                <div style="font-weight: 700; color: var(--text-primary); font-size: 1rem;">📅 ${formatDate(nextB.booking_date)}</div>
              </div>
              <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Time Slot</div>
                <div style="font-weight: 700; color: var(--text-primary); font-size: 1rem;">⏰ ${nextB.slot_time}</div>
              </div>
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
              <a href="/turf/${nextB.turf_id}" class="btn btn-secondary btn-sm">Turf Info</a>
              <a href="/bookings" class="btn btn-primary btn-sm">Manage Reservation</a>
            </div>
          </div>
        `;
      } else {
        nextMatchContainer.innerHTML = `
          <div class="card" style="padding: 2rem; text-align: center; border: 1px dashed var(--border-subtle);">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">⚽</div>
            <h3 style="font-size: 1.2rem; font-weight: 700; margin-bottom: 0.3rem;">No Upcoming Matches Scheduled</h3>
            <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.2rem;">Ready to hit the ground with your squad? Book a slot at top rated arenas.</p>
            <a href="/turfs" class="btn btn-primary btn-sm">Find & Book Turf</a>
          </div>
        `;
      }
    }

    // Render Recent Bookings Table
    const recentTableBody = document.getElementById('recent-bookings-tbody');
    if (recentTableBody) {
      if (bookings.length === 0) {
        recentTableBody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No booking history available.</td>
          </tr>
        `;
      } else {
        recentTableBody.innerHTML = bookings.slice(0, 4).map(b => {
          let badge = 'badge-emerald';
          if (b.status === 'CANCELLED') badge = 'badge-red';
          if (b.status === 'COMPLETED') badge = 'badge-blue';

          return `
            <tr>
              <td style="font-family: monospace; font-weight: 700; color: var(--primary);">${b.booking_reference}</td>
              <td style="font-weight: 600;">${b.turf_name}</td>
              <td>${formatDate(b.booking_date)}</td>
              <td>${b.slot_time}</td>
              <td style="font-weight: 700; color: #34d399;">₹${b.price}</td>
              <td><span class="badge ${badge}">${b.status}</span></td>
            </tr>
          `;
        }).join('');
      }
    }
  }

  // Load Recommended Turfs
  const recContainer = document.getElementById('dashboard-recommended-turfs');
  if (recContainer) {
    const turfsRes = await API.get('/turfs', { sort: 'rating_desc' });
    if (turfsRes.ok && turfsRes.data && turfsRes.data.turfs) {
      const turfs = turfsRes.data.turfs.slice(0, 3);
      recContainer.innerHTML = turfs.map(t => `
        <div class="card turf-card">
          <div class="turf-card-img-wrap" style="height: 150px;">
            <img src="${t.image_url}" alt="${t.name}">
            <div class="turf-card-overlay">
              <span class="badge badge-emerald">⭐ ${t.rating}</span>
            </div>
          </div>
          <div class="turf-card-body" style="padding: 1rem;">
            <h4 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 0.25rem;">${t.name}</h4>
            <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.75rem;">📍 ${t.location}</div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: auto;">
              <span style="font-weight: 800; color: #34d399;">₹${t.price_per_hour}/hr</span>
              <a href="/turf/${t.id}" class="btn btn-primary btn-sm">Book</a>
            </div>
          </div>
        </div>
      `).join('');
    }
  }
});
