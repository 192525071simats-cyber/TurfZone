/**
 * Tournament Marketplace & Team Registration Logic
 */

let allTournaments = [];
let activeTournamentForReg = null;

async function loadTournaments() {
  const container = document.getElementById('tournaments-grid-container');
  if (!container) return;

  container.innerHTML = '<div class="spinner" style="grid-column: 1 / -1;"></div>';

  const sport = document.getElementById('tournament-sport-filter')?.value || 'all';
  const status = document.getElementById('tournament-status-filter')?.value || 'ALL';

  const params = {};
  if (sport !== 'all') params.sport = sport;
  if (status !== 'ALL') params.status = status;

  const res = await API.get('/tournaments', params);
  if (res.ok && res.data) {
    allTournaments = res.data.tournaments || [];
    renderTournaments(allTournaments);
  } else {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-state-icon">⚠️</div>
        <div class="empty-state-title">Unable to Load Tournaments</div>
        <div class="empty-state-text">${res.message || 'Error fetching tournament list.'}</div>
        <button onclick="loadTournaments()" class="btn btn-primary btn-sm">Retry</button>
      </div>
    `;
  }
}

function renderTournaments(tournaments) {
  const container = document.getElementById('tournaments-grid-container');
  if (!container) return;

  if (tournaments.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-state-icon">🏆</div>
        <div class="empty-state-title">No Tournaments Found</div>
        <div class="empty-state-text">No active tournaments matched your selected filters.</div>
      </div>
    `;
    return;
  }

  container.innerHTML = tournaments.map(t => {
    let badgeClass = 'badge-emerald';
    let canRegister = t.status === 'OPEN';
    let statusLabel = 'OPEN FOR REGISTRATION';

    if (t.status === 'FULL') {
      badgeClass = 'badge-amber';
      statusLabel = 'SLOTS FULL';
    } else if (t.status === 'CLOSED') {
      badgeClass = 'badge-red';
      statusLabel = 'REGISTRATION CLOSED';
    } else if (t.status === 'COMPLETED') {
      badgeClass = 'badge-blue';
      statusLabel = 'COMPLETED';
    }

    const percentFilled = Math.min(100, Math.round((t.registered_teams / t.max_teams) * 100));

    return `
      <div class="card" style="display: flex; flex-direction: column;">
        <div style="position: relative; height: 180px; overflow: hidden;">
          <img src="${t.image_url}" alt="${t.name}" style="width: 100%; height: 100%; object-fit: cover;">
          <div style="position: absolute; top: 12px; left: 12px; right: 12px; display: flex; justify-content: space-between;">
            <span class="badge badge-purple">🏆 ${t.sport}</span>
            <span class="badge ${badgeClass}">${statusLabel}</span>
          </div>
        </div>

        <div style="padding: 1.5rem; display: flex; flex-direction: column; flex-grow: 1;">
          <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem; color: var(--text-primary);">${t.name}</h3>
          
          <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 1rem; display: flex; flex-direction: column; gap: 0.3rem;">
            <div>📍 <strong>Venue:</strong> ${t.venue}</div>
            <div>📅 <strong>Date:</strong> ${formatDate(t.tournament_date)}</div>
            <div>⏰ <strong>Deadline:</strong> ${formatDate(t.registration_deadline)}</div>
          </div>

          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem; line-height: 1.5;">
            ${t.description}
          </p>

          <!-- Capacity Bar -->
          <div style="margin-bottom: 1.25rem;">
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.35rem;">
              <span>Teams Registered</span>
              <span><strong>${t.registered_teams}</strong> / ${t.max_teams} (${t.remaining_slots} slots left)</span>
            </div>
            <div style="width: 100%; height: 6px; background: var(--bg-surface); border-radius: 3px; overflow: hidden;">
              <div style="width: ${percentFilled}%; height: 100%; background: linear-gradient(90deg, var(--primary), var(--accent-cyan));"></div>
            </div>
          </div>

          <div style="margin-top: auto; display: flex; justify-content: space-between; align-items: center; padding-top: 1rem; border-top: 1px solid var(--border-subtle);">
            <div>
              <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Entry Fee</div>
              <div style="font-size: 1.3rem; font-weight: 800; color: #34d399;">₹${t.entry_fee}</div>
            </div>
            <button 
              onclick="openTournamentRegModal(${t.id})" 
              class="btn ${canRegister ? 'btn-primary' : 'btn-secondary'} btn-sm"
              ${canRegister ? '' : 'disabled'}
            >
              ${canRegister ? 'Register Team' : 'Registration Unavailable'}
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function openTournamentRegModal(tournamentId) {
  if (!Auth.isLoggedIn()) {
    Toast.warning('Please log in to register your team.');
    window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
    return;
  }

  activeTournamentForReg = allTournaments.find(t => t.id === tournamentId);
  if (!activeTournamentForReg) return;

  const user = Auth.getUser();

  document.getElementById('treg-tourn-name').textContent = activeTournamentForReg.name;
  document.getElementById('treg-tourn-fee').textContent = `₹${activeTournamentForReg.entry_fee}`;
  document.getElementById('treg-tourn-deadline').textContent = formatDate(activeTournamentForReg.registration_deadline);

  // Pre-fill Captain & Contact from User Profile
  const captainInput = document.getElementById('treg-captain-name');
  const contactInput = document.getElementById('treg-contact');
  if (captainInput && !captainInput.value) captainInput.value = user.name;
  if (contactInput && !contactInput.value) contactInput.value = user.phone;

  openModal('tournament-reg-modal');
}

async function submitTournamentRegistration(e) {
  e.preventDefault();
  if (!activeTournamentForReg) return;

  const teamName = document.getElementById('treg-team-name').value.trim();
  const captainName = document.getElementById('treg-captain-name').value.trim();
  const contact = document.getElementById('treg-contact').value.trim();
  const playerCount = document.getElementById('treg-player-count').value;
  const players = document.getElementById('treg-players-list').value.trim();

  const submitBtn = document.getElementById('treg-submit-btn');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = 'Submitting Registration...';
  }

  const payload = {
    team_name: teamName,
    captain_name: captainName,
    contact: contact,
    player_count: playerCount,
    players: players
  };

  const res = await API.post(`/tournaments/${activeTournamentForReg.id}/register`, payload);

  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.innerHTML = 'Register Team & Confirm';
  }

  if (res.ok && res.data && res.data.registration) {
    closeModal('tournament-reg-modal');
    
    // Show success modal
    const reg = res.data.registration;
    document.getElementById('treg-success-ref').textContent = reg.registration_reference;
    document.getElementById('treg-success-team').textContent = reg.team_name;
    document.getElementById('treg-success-tourn').textContent = reg.tournament_name;
    openModal('tournament-success-modal');

    // Reload tournaments
    loadTournaments();
  } else {
    Toast.error(res.message || 'Registration failed.');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('tournament-sport-filter')?.addEventListener('change', loadTournaments);
  document.getElementById('tournament-status-filter')?.addEventListener('change', loadTournaments);
  document.getElementById('tournament-reg-form')?.addEventListener('submit', submitTournamentRegistration);

  loadTournaments();
});
