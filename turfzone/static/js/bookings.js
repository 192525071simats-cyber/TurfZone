/**
 * My Bookings Management Logic with Match Pass E-Ticket and Squad Bill Splitter
 */

let allBookings = [];
let currentFilter = 'all';
let bookingToCancel = null;
let currentBookingForPass = null;

async function loadUserBookings() {
  if (!Auth.requireAuth()) return;

  const container = document.getElementById('bookings-list-container');
  if (!container) return;

  container.innerHTML = '<div class="spinner"></div>';

  const res = await API.get('/bookings');
  if (res.ok && res.data) {
    allBookings = res.data.bookings || [];
    renderBookings();
    updateTabCounts();
  } else {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⚠️</div>
        <div class="empty-state-title">Unable to Load Bookings</div>
        <div class="empty-state-text">${res.message || 'Error communicating with server.'}</div>
        <button onclick="loadUserBookings()" class="btn btn-primary btn-sm">Retry</button>
      </div>
    `;
  }
}

function updateTabCounts() {
  const today = new Date().toISOString().split('T')[0];
  
  const upcomingCount = allBookings.filter(b => b.status === 'CONFIRMED' && b.booking_date > today).length;
  const currentCount = allBookings.filter(b => b.status === 'CONFIRMED' && b.booking_date === today).length;
  const previousCount = allBookings.filter(b => b.status === 'CANCELLED' || b.status === 'COMPLETED' || (b.status === 'CONFIRMED' && b.booking_date < today)).length;

  const allBadge = document.getElementById('count-all');
  const upcomingBadge = document.getElementById('count-upcoming');
  const currentBadge = document.getElementById('count-current');
  const prevBadge = document.getElementById('count-previous');

  if (allBadge) allBadge.textContent = allBookings.length;
  if (upcomingBadge) upcomingBadge.textContent = upcomingCount;
  if (currentBadge) currentBadge.textContent = currentCount;
  if (prevBadge) prevBadge.textContent = previousCount;
}

function filterTab(tab) {
  currentFilter = tab;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });
  renderBookings();
}

function renderBookings() {
  const container = document.getElementById('bookings-list-container');
  if (!container) return;

  const today = new Date().toISOString().split('T')[0];

  let filtered = allBookings;
  if (currentFilter === 'upcoming') {
    filtered = allBookings.filter(b => b.status === 'CONFIRMED' && b.booking_date > today);
  } else if (currentFilter === 'current') {
    filtered = allBookings.filter(b => b.status === 'CONFIRMED' && b.booking_date === today);
  } else if (currentFilter === 'previous') {
    filtered = allBookings.filter(b => b.status === 'CANCELLED' || b.status === 'COMPLETED' || (b.status === 'CONFIRMED' && b.booking_date < today));
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <div class="empty-state-title">No Bookings Found</div>
        <div class="empty-state-text">You don't have any bookings matching this category. Ready to play?</div>
        <a href="/turfs" class="btn btn-primary btn-sm">Explore & Book Turfs</a>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(b => {
    let badgeClass = 'badge-emerald';
    if (b.status === 'CANCELLED') badgeClass = 'badge-red';
    if (b.status === 'COMPLETED') badgeClass = 'badge-blue';

    const isConfirmed = b.status === 'CONFIRMED';
    const canCancel = isConfirmed && b.booking_date >= today;

    return `
      <div class="card" style="margin-bottom: 1.25rem; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
          <div>
            <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.3rem;">
              <span style="font-weight: 800; font-size: 1.1rem; color: var(--text-primary);">${b.turf_name}</span>
              <span class="badge ${badgeClass}">${b.status}</span>
            </div>
            <div style="color: var(--text-secondary); font-size: 0.875rem;">
              📍 ${b.turf_location} • 🏆 ${b.sport}
            </div>
          </div>
          <div style="text-align: right;">
            <div style="font-family: monospace; font-size: 0.9rem; font-weight: 700; color: var(--primary);">${b.booking_reference}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">Booked on ${b.created_at ? b.created_at.split(' ')[0] : 'Recently'}</div>
          </div>
        </div>

        <div style="background: var(--bg-surface); border-radius: var(--radius-md); padding: 1rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 1rem;">
          <div>
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Date</div>
            <div style="font-weight: 600; font-size: 0.95rem; color: var(--text-primary);">${formatDate(b.booking_date)}</div>
          </div>
          <div>
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Time Slot</div>
            <div style="font-weight: 600; font-size: 0.95rem; color: var(--text-primary);">${b.slot_time}</div>
          </div>
          <div>
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Amount Paid</div>
            <div style="font-weight: 700; font-size: 1.1rem; color: #34d399;">₹${b.price}</div>
          </div>
          ${b.addons && b.addons.length > 0 ? `
            <div>
              <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Extras</div>
              <div style="font-size: 0.85rem; color: var(--accent-cyan); font-weight: 600;">${b.addons.join(', ')}</div>
            </div>
          ` : ''}
        </div>

        <div style="display: flex; justify-content: flex-end; align-items: center; gap: 0.75rem; padding-top: 0.5rem; flex-wrap: wrap;">
          <a href="/turf/${b.turf_id}" class="btn btn-secondary btn-sm">View Turf</a>
          
          ${isConfirmed ? `
            <button onclick="openMatchPassModal(${JSON.stringify(b).replace(/"/g, '&quot;')})" class="btn btn-primary btn-sm">
              🎫 Match Pass
            </button>
            <button onclick="openSquadShareModal(${JSON.stringify(b).replace(/"/g, '&quot;')})" class="btn btn-secondary btn-sm">
              👥 Invite Squad
            </button>
          ` : ''}

          ${canCancel ? `
            <button onclick="promptCancelBooking(${b.id}, '${b.booking_reference}', '${b.turf_name}')" class="btn btn-outline btn-sm" style="border-color: var(--accent-red); color: var(--accent-red);">
              Cancel
            </button>
          ` : ''}
        </div>
      </div>
    `;
  }).join('');
}

function promptCancelBooking(id, ref, turfName) {
  bookingToCancel = id;
  document.getElementById('cancel-modal-ref').textContent = ref;
  document.getElementById('cancel-modal-turf').textContent = turfName;
  openModal('cancel-confirm-modal');
}

async function confirmCancelBooking() {
  if (!bookingToCancel) return;

  const btn = document.getElementById('confirm-cancel-btn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = 'Cancelling...';
  }

  const res = await API.put(`/bookings/${bookingToCancel}/cancel`);

  if (btn) {
    btn.disabled = false;
    btn.innerHTML = 'Yes, Cancel Reservation';
  }

  if (res.ok) {
    Toast.success(res.message || 'Booking cancelled successfully.');
    closeModal('cancel-confirm-modal');
    bookingToCancel = null;
    loadUserBookings();
  } else {
    Toast.error(res.message || 'Failed to cancel booking.');
  }
}

// -------------------------------------------------------------
// DIGITAL MATCH PASS / E-TICKET
// -------------------------------------------------------------
function openMatchPassModal(booking) {
  currentBookingForPass = booking;
  
  document.getElementById('pass-turf-name').textContent = booking.turf_name;
  document.getElementById('pass-turf-addr').textContent = booking.turf_address || booking.turf_location;
  document.getElementById('pass-ref').textContent = booking.booking_reference;
  document.getElementById('pass-date').textContent = formatDate(booking.booking_date);
  document.getElementById('pass-time').textContent = booking.slot_time;
  document.getElementById('pass-sport').textContent = booking.sport;
  document.getElementById('pass-amount').textContent = `₹${booking.price}`;
  document.getElementById('pass-player').textContent = booking.user_name || 'Athletic Member';

  // Render SVG QR Code
  const qrWrap = document.getElementById('pass-qr-code');
  if (qrWrap) {
    qrWrap.innerHTML = `
      <svg viewBox="0 0 100 100" width="100%" height="100%">
        <rect width="100" height="100" fill="#ffffff" />
        <path d="M10,10 h30 v30 h-30 z M15,15 v20 h20 v-20 z M20,20 h10 v10 h-10 z" fill="#000000" />
        <path d="M60,10 h30 v30 h-30 z M65,15 v20 h20 v-20 z M70,20 h10 v10 h-10 z" fill="#000000" />
        <path d="M10,60 h30 v30 h-30 z M15,65 v20 h20 v-20 z M20,70 h10 v10 h-10 z" fill="#000000" />
        <rect x="45" y="15" width="8" height="8" fill="#000" />
        <rect x="45" y="30" width="8" height="8" fill="#000" />
        <rect x="45" y="45" width="8" height="8" fill="#000" />
        <rect x="60" y="45" width="12" height="8" fill="#000" />
        <rect x="75" y="55" width="15" height="8" fill="#000" />
        <rect x="55" y="70" width="10" height="15" fill="#000" />
        <rect x="75" y="75" width="15" height="15" fill="#000" />
      </svg>
    `;
  }

  openModal('match-pass-modal');
}

function printMatchPass() {
  window.print();
}

// -------------------------------------------------------------
// SQUAD INVITE & BILL SPLITTER
// -------------------------------------------------------------
function openSquadShareModal(booking) {
  document.getElementById('split-total-amount').textContent = `₹${booking.price}`;
  
  const playerSlider = document.getElementById('split-player-count');
  const countDisplay = document.getElementById('split-count-display');
  const shareDisplay = document.getElementById('split-per-player');

  function recalc() {
    const players = parseInt(playerSlider.value);
    countDisplay.textContent = `${players} Players`;
    const share = Math.ceil(booking.price / players);
    shareDisplay.textContent = `₹${share}`;

    // Generate Share Message
    const shareText = `⚽ Match Alert with Squad!\n📍 Venue: ${booking.turf_name} (${booking.turf_location})\n📅 Date: ${formatDate(booking.booking_date)}\n⏰ Slot: ${booking.slot_time} (${booking.sport})\n💰 Split Share: ₹${share} per player\n🎫 Booking ID: ${booking.booking_reference}\n\nLet's play! See you at the turf!`;
    document.getElementById('squad-share-text').value = shareText;
  }

  playerSlider.oninput = recalc;
  recalc();

  openModal('squad-share-modal');
}

function copySquadInvite() {
  const textarea = document.getElementById('squad-share-text');
  textarea.select();
  document.execCommand('copy');
  Toast.success('Match invite copied to clipboard! Paste in your team WhatsApp group.');
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => filterTab(btn.dataset.tab));
  });

  loadUserBookings();
});
