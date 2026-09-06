/**
 * Admin Control Center Management Logic
 */

let adminStats = null;
let currentAdminTab = 'overview';

async function initAdminDashboard() {
  if (!Auth.requireAdmin()) return;

  await loadAdminStats();
  setupAdminTabs();
}

async function loadAdminStats() {
  const res = await API.get('/admin/stats');
  if (res.ok && res.data) {
    adminStats = res.data.stats;
    renderStatsMetrics(adminStats);
    renderRecentBookingsTable(res.data.recent_bookings || []);
    renderRecentUsersTable(res.data.recent_users || []);
  } else {
    Toast.error('Failed to load admin statistics.');
  }
}

function renderStatsMetrics(stats) {
  document.getElementById('admin-stat-revenue').textContent = `₹${stats.total_revenue.toLocaleString()}`;
  document.getElementById('admin-stat-bookings').textContent = stats.total_bookings;
  document.getElementById('admin-stat-turfs').textContent = `${stats.active_turfs} / ${stats.total_turfs}`;
  document.getElementById('admin-stat-users').textContent = stats.total_users;
  document.getElementById('admin-stat-today-bookings').textContent = stats.todays_bookings;
  document.getElementById('admin-stat-tourn-regs').textContent = stats.total_tournament_registrations;
}

function renderRecentBookingsTable(bookings) {
  const tbody = document.getElementById('admin-recent-bookings-tbody');
  if (!tbody) return;

  if (bookings.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No recent bookings.</td></tr>';
    return;
  }

  tbody.innerHTML = bookings.map(b => {
    let badge = 'badge-emerald';
    if (b.status === 'CANCELLED') badge = 'badge-red';
    if (b.status === 'COMPLETED') badge = 'badge-blue';

    return `
      <tr>
        <td style="font-family: monospace; font-weight: 700; color: var(--primary);">${b.booking_reference}</td>
        <td>${b.user_name || 'User #' + b.user_id}</td>
        <td>${b.turf_name}</td>
        <td>${formatDate(b.booking_date)} (${b.slot_time})</td>
        <td style="font-weight: 700; color: #34d399;">₹${b.price}</td>
        <td><span class="badge ${badge}">${b.status}</span></td>
      </tr>
    `;
  }).join('');
}

function renderRecentUsersTable(users) {
  const tbody = document.getElementById('admin-recent-users-tbody');
  if (!tbody) return;

  if (users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No registered users.</td></tr>';
    return;
  }

  tbody.innerHTML = users.map(u => `
    <tr>
      <td style="font-weight: 600;">${u.name}</td>
      <td>${u.email}</td>
      <td>${u.phone}</td>
      <td><span class="badge ${u.role === 'ADMIN' ? 'badge-amber' : 'badge-emerald'}">${u.role}</span></td>
      <td>${u.created_at ? u.created_at.split(' ')[0] : 'Recently'}</td>
    </tr>
  `).join('');
}

function setupAdminTabs() {
  document.querySelectorAll('.admin-nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.admin-nav-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const tab = btn.dataset.tab;
      currentAdminTab = tab;

      document.querySelectorAll('.admin-tab-section').forEach(sec => sec.style.display = 'none');
      const activeSec = document.getElementById(`admin-tab-${tab}`);
      if (activeSec) activeSec.style.display = 'block';

      if (tab === 'turfs') loadAdminTurfs();
      if (tab === 'bookings') loadAdminBookings();
      if (tab === 'tournaments') loadAdminTournaments();
      if (tab === 'users') loadAdminUsers();
    });
  });
}

// -------------------------------------------------------------
// TAB 2: TURF MANAGEMENT
// -------------------------------------------------------------
async function loadAdminTurfs() {
  const tbody = document.getElementById('admin-turfs-tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem;"><div class="spinner"></div></td></tr>';

  const res = await API.get('/turfs', { include_inactive: true });
  if (res.ok && res.data) {
    const turfs = res.data.turfs || [];
    if (turfs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No turfs created yet.</td></tr>';
      return;
    }

    tbody.innerHTML = turfs.map(t => `
      <tr>
        <td style="font-weight: 700; color: var(--text-primary);">${t.name}</td>
        <td>${t.location}</td>
        <td>${t.sport}</td>
        <td style="font-weight: 700; color: #34d399;">₹${t.price_per_hour}/hr</td>
        <td>⭐ ${t.rating}</td>
        <td><span class="badge ${t.is_active ? 'badge-emerald' : 'badge-red'}">${t.is_active ? 'ACTIVE' : 'INACTIVE'}</span></td>
        <td>
          <div style="display: flex; gap: 0.4rem;">
            <button onclick="openEditTurfModal(${JSON.stringify(t).replace(/"/g, '&quot;')})" class="btn btn-secondary btn-sm">Edit</button>
            <button onclick="deleteTurf(${t.id}, '${t.name.replace(/'/g, "\\'")}')" class="btn btn-outline btn-sm" style="border-color: var(--accent-red); color: var(--accent-red);">Delete</button>
          </div>
        </td>
      </tr>
    `).join('');
  }
}

function openAddTurfModal() {
  document.getElementById('turf-modal-title').textContent = 'Add New Sports Turf';
  document.getElementById('turf-form-id').value = '';
  document.getElementById('turf-form-name').value = '';
  document.getElementById('turf-form-location').value = '';
  document.getElementById('turf-form-address').value = '';
  document.getElementById('turf-form-sport').value = 'Football, Cricket';
  document.getElementById('turf-form-price').value = '1200';
  document.getElementById('turf-form-facilities').value = 'Floodlights, Parking, Changing Rooms, Washrooms, Drinking Water';
  document.getElementById('turf-form-image').value = 'https://images.unsplash.com/photo-1529900245534-47fbf8221565?auto=format&fit=crop&w=1200&q=80';
  document.getElementById('turf-form-desc').value = '';
  document.getElementById('turf-form-active').checked = true;

  openModal('admin-turf-modal');
}

function openEditTurfModal(turf) {
  document.getElementById('turf-modal-title').textContent = `Edit Turf: ${turf.name}`;
  document.getElementById('turf-form-id').value = turf.id;
  document.getElementById('turf-form-name').value = turf.name;
  document.getElementById('turf-form-location').value = turf.location;
  document.getElementById('turf-form-address').value = turf.address;
  document.getElementById('turf-form-sport').value = turf.sport;
  document.getElementById('turf-form-price').value = turf.price_per_hour;
  document.getElementById('turf-form-facilities').value = Array.isArray(turf.facilities) ? turf.facilities.join(', ') : turf.facilities;
  document.getElementById('turf-form-image').value = turf.image_url;
  document.getElementById('turf-form-desc').value = turf.description;
  document.getElementById('turf-form-active').checked = turf.is_active;

  openModal('admin-turf-modal');
}

async function saveTurfForm(e) {
  e.preventDefault();
  const id = document.getElementById('turf-form-id').value;
  const payload = {
    name: document.getElementById('turf-form-name').value.trim(),
    location: document.getElementById('turf-form-location').value.trim(),
    address: document.getElementById('turf-form-address').value.trim(),
    sport: document.getElementById('turf-form-sport').value.trim(),
    price_per_hour: parseFloat(document.getElementById('turf-form-price').value),
    facilities: document.getElementById('turf-form-facilities').value.trim(),
    image_url: document.getElementById('turf-form-image').value.trim(),
    description: document.getElementById('turf-form-desc').value.trim(),
    is_active: document.getElementById('turf-form-active').checked
  };

  let res;
  if (id) {
    res = await API.put(`/turfs/${id}`, payload);
  } else {
    res = await API.post('/turfs', payload);
  }

  if (res.ok) {
    Toast.success(res.message || 'Turf saved successfully.');
    closeModal('admin-turf-modal');
    loadAdminTurfs();
    loadAdminStats();
  } else {
    Toast.error(res.message || 'Failed to save turf.');
  }
}

async function deleteTurf(id, name) {
  if (!confirm(`Are you sure you want to remove or deactivate turf "${name}"?`)) return;

  const res = await API.delete(`/turfs/${id}`);
  if (res.ok) {
    Toast.success(res.message || 'Turf updated successfully.');
    loadAdminTurfs();
    loadAdminStats();
  } else {
    Toast.error(res.message || 'Failed to delete turf.');
  }
}

// -------------------------------------------------------------
// TAB 3: BOOKINGS MANAGEMENT
// -------------------------------------------------------------
async function loadAdminBookings() {
  const tbody = document.getElementById('admin-all-bookings-tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem;"><div class="spinner"></div></td></tr>';

  const res = await API.get('/admin/bookings');
  if (res.ok && res.data) {
    const bookings = res.data.bookings || [];
    if (bookings.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No bookings found in database.</td></tr>';
      return;
    }

    tbody.innerHTML = bookings.map(b => `
      <tr>
        <td style="font-family: monospace; font-weight: 700; color: var(--primary);">${b.booking_reference}</td>
        <td>
          <div style="font-weight: 600;">${b.user_name || 'User #' + b.user_id}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${b.user_email || ''}</div>
        </td>
        <td>${b.turf_name}</td>
        <td>${formatDate(b.booking_date)} (${b.slot_time})</td>
        <td style="font-weight: 700; color: #34d399;">₹${b.price}</td>
        <td>
          <select onchange="updateBookingStatus(${b.id}, this.value)" class="form-control" style="padding: 0.3rem 0.6rem; font-size: 0.85rem; width: auto;">
            <option value="CONFIRMED" ${b.status === 'CONFIRMED' ? 'selected' : ''}>CONFIRMED</option>
            <option value="COMPLETED" ${b.status === 'COMPLETED' ? 'selected' : ''}>COMPLETED</option>
            <option value="CANCELLED" ${b.status === 'CANCELLED' ? 'selected' : ''}>CANCELLED</option>
          </select>
        </td>
      </tr>
    `).join('');
  }
}

async function updateBookingStatus(id, newStatus) {
  const res = await API.put(`/admin/bookings/${id}/status`, { status: newStatus });
  if (res.ok) {
    Toast.success(res.message || 'Booking status updated.');
    loadAdminStats();
  } else {
    Toast.error(res.message || 'Failed to update status.');
    loadAdminBookings();
  }
}

// -------------------------------------------------------------
// TAB 4: TOURNAMENT MANAGEMENT
// -------------------------------------------------------------
async function loadAdminTournaments() {
  const tbody = document.getElementById('admin-tournaments-tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem;"><div class="spinner"></div></td></tr>';

  const res = await API.get('/tournaments');
  if (res.ok && res.data) {
    const tourns = res.data.tournaments || [];
    if (tourns.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No tournaments created.</td></tr>';
      return;
    }

    tbody.innerHTML = tourns.map(t => `
      <tr>
        <td style="font-weight: 700;">${t.name}</td>
        <td>${t.sport}</td>
        <td>${t.venue}</td>
        <td>${formatDate(t.tournament_date)}</td>
        <td><strong>${t.registered_teams}</strong> / ${t.max_teams}</td>
        <td><span class="badge badge-emerald">${t.status}</span></td>
        <td>
          <button onclick="deleteTournament(${t.id}, '${t.name.replace(/'/g, "\\'")}')" class="btn btn-outline btn-sm" style="border-color: var(--accent-red); color: var(--accent-red);">Delete</button>
        </td>
      </tr>
    `).join('');
  }
}

function openAddTournamentModal() {
  document.getElementById('tourn-modal-title').textContent = 'Create New Tournament';
  document.getElementById('tourn-form-name').value = '';
  document.getElementById('tourn-form-sport').value = 'Football';
  document.getElementById('tourn-form-venue').value = 'Marina Champions Arena';
  
  const today = new Date();
  const tDate = new Date(today.getTime() + 15 * 86400000).toISOString().split('T')[0];
  const dDate = new Date(today.getTime() + 10 * 86400000).toISOString().split('T')[0];

  document.getElementById('tourn-form-date').value = tDate;
  document.getElementById('tourn-form-deadline').value = dDate;
  document.getElementById('tourn-form-fee').value = '2500';
  document.getElementById('tourn-form-teams').value = '16';
  document.getElementById('tourn-form-desc').value = 'Exciting city-wide sports tournament with trophy and prizes.';
  document.getElementById('tourn-form-image').value = 'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=800&q=80';

  openModal('admin-tourn-modal');
}

async function saveTournamentForm(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById('tourn-form-name').value.trim(),
    sport: document.getElementById('tourn-form-sport').value.trim(),
    venue: document.getElementById('tourn-form-venue').value.trim(),
    tournament_date: document.getElementById('tourn-form-date').value,
    registration_deadline: document.getElementById('tourn-form-deadline').value,
    entry_fee: parseFloat(document.getElementById('tourn-form-fee').value),
    max_teams: parseInt(document.getElementById('tourn-form-teams').value),
    description: document.getElementById('tourn-form-desc').value.trim(),
    image_url: document.getElementById('tourn-form-image').value.trim()
  };

  const res = await API.post('/tournaments', payload);
  if (res.ok) {
    Toast.success('Tournament created successfully!');
    closeModal('admin-tourn-modal');
    loadAdminTournaments();
    loadAdminStats();
  } else {
    Toast.error(res.message || 'Failed to create tournament.');
  }
}

async function deleteTournament(id, name) {
  if (!confirm(`Are you sure you want to delete tournament "${name}"?`)) return;

  const res = await API.delete(`/tournaments/${id}`);
  if (res.ok) {
    Toast.success('Tournament deleted successfully.');
    loadAdminTournaments();
    loadAdminStats();
  } else {
    Toast.error(res.message || 'Failed to delete tournament.');
  }
}

// -------------------------------------------------------------
// TAB 5: USER MANAGEMENT
// -------------------------------------------------------------
async function loadAdminUsers() {
  const tbody = document.getElementById('admin-users-tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem;"><div class="spinner"></div></td></tr>';

  const res = await API.get('/admin/users');
  if (res.ok && res.data) {
    const users = res.data.users || [];
    tbody.innerHTML = users.map(u => `
      <tr>
        <td style="font-weight: 700;">${u.name}</td>
        <td>${u.email}</td>
        <td>${u.phone}</td>
        <td><span class="badge ${u.role === 'ADMIN' ? 'badge-amber' : 'badge-emerald'}">${u.role}</span></td>
        <td>${u.booking_count} Bookings</td>
        <td><span class="badge ${u.is_active ? 'badge-emerald' : 'badge-red'}">${u.is_active ? 'ACTIVE' : 'DEACTIVATED'}</span></td>
        <td>
          ${u.role !== 'ADMIN' ? `
            <button onclick="toggleUserStatus(${u.id}, ${u.is_active})" class="btn btn-secondary btn-sm">
              ${u.is_active ? 'Deactivate' : 'Activate'}
            </button>
          ` : '<span style="color: var(--text-muted); font-size: 0.8rem;">Protected</span>'}
        </td>
      </tr>
    `).join('');
  }
}

async function toggleUserStatus(id, currentActive) {
  const res = await API.put(`/admin/users/${id}/toggle-status`);
  if (res.ok) {
    Toast.success(res.message || 'User status updated.');
    loadAdminUsers();
  } else {
    Toast.error(res.message || 'Failed to update user status.');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initAdminDashboard();
  document.getElementById('admin-turf-form')?.addEventListener('submit', saveTurfForm);
  document.getElementById('admin-tourn-form')?.addEventListener('submit', saveTournamentForm);
});
