/**
 * Turf Detail & Real-Time Slot Booking Engine with Add-ons and Reviews
 */

let currentTurf = null;
let selectedDate = null;
let selectedSlot = null;
let selectedSport = null;
let selectedAddons = [];
let currentReviewRating = 5;

async function initTurfDetail(turfId) {
  const container = document.getElementById('turf-detail-container');
  if (!container) return;

  const res = await API.get(`/turfs/${turfId}`);
  if (!res.ok || !res.data || !res.data.turf) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">❌</div>
        <div class="empty-state-title">Turf Not Found</div>
        <div class="empty-state-text">The requested sports facility could not be found.</div>
        <a href="/turfs" class="btn btn-primary btn-sm">Explore Other Turfs</a>
      </div>
    `;
    return;
  }

  currentTurf = res.data.turf;
  renderTurfOverview(currentTurf);

  // Initialize Date Picker (Min = Today, Default = Today in Local Time)
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  const dateInput = document.getElementById('booking-date-picker');
  if (dateInput) {
    dateInput.min = todayStr;
    dateInput.value = todayStr;
    selectedDate = todayStr;
    dateInput.addEventListener('change', (e) => {
      selectedDate = e.target.value;
      selectedSlot = null;
      updateBookingSummary();
      loadAvailability(currentTurf.id, selectedDate);
    });
  }

  updateBookingSummary();

  // Load initial availability and reviews
  await loadAvailability(currentTurf.id, selectedDate || todayStr);
  await loadTurfReviews(currentTurf.id);
  setupReviewForm(currentTurf.id);
  setupAddonListeners();
}

function renderTurfOverview(turf) {
  document.title = `${turf.name} — TurfZone`;

  const sports = turf.sport.split(',').map(s => s.trim());
  selectedSport = sports[0] || 'Football';

  // Sport selector options in summary
  const sportSelect = document.getElementById('booking-sport-select');
  if (sportSelect) {
    sportSelect.innerHTML = sports.map(s => `<option value="${s}">${s}</option>`).join('');
    sportSelect.addEventListener('change', (e) => {
      selectedSport = e.target.value;
      updateBookingSummary();
    });
  }

  // Populate Details
  const nameElem = document.getElementById('turf-name');
  const locElem = document.getElementById('turf-location');
  const addrElem = document.getElementById('turf-address');
  const ratingElem = document.getElementById('turf-rating');
  const descElem = document.getElementById('turf-desc');
  const heroImg = document.getElementById('turf-hero-img');
  const sportsWrap = document.getElementById('turf-sports-tags');
  const amenitiesList = document.getElementById('turf-amenities-list');
  const priceElem = document.getElementById('turf-rate-display');

  if (nameElem) nameElem.textContent = turf.name;
  if (locElem) locElem.textContent = turf.location;
  if (addrElem) addrElem.textContent = turf.address;
  if (ratingElem) ratingElem.innerHTML = `⭐ ${turf.rating} <span>(${turf.reviews_count} reviews)</span>`;
  if (descElem) descElem.textContent = turf.description;
  if (heroImg) heroImg.src = turf.image_url;
  if (priceElem) priceElem.textContent = `₹${turf.price_per_hour}`;

  if (sportsWrap) {
    sportsWrap.innerHTML = sports.map(s => `<span class="badge badge-purple" style="font-size: 0.85rem;">${s}</span>`).join('');
  }

  if (amenitiesList) {
    amenitiesList.innerHTML = turf.facilities.map(f => `
      <li style="display: flex; align-items: center; gap: 0.5rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
        <span style="color: var(--primary);">✓</span> ${f}
      </li>
    `).join('');
  }

  updateBookingSummary();
}

function setupAddonListeners() {
  document.querySelectorAll('.addon-checkbox').forEach(cb => {
    cb.addEventListener('change', () => {
      selectedAddons = Array.from(document.querySelectorAll('.addon-checkbox:checked')).map(c => c.value);
      updateBookingSummary();
    });
  });
}

async function loadAvailability(turfId, dateStr) {
  const slotsContainer = document.getElementById('slots-container');
  const slotCountBadge = document.getElementById('slot-count-badge');
  if (!slotsContainer) return;

  slotsContainer.innerHTML = '<div class="spinner" style="grid-column: 1 / -1;"></div>';

  const res = await API.get(`/turfs/${turfId}/availability`, { date: dateStr });
  if (res.ok && res.data) {
    const slots = res.data.slots || [];
    if (slotCountBadge) {
      slotCountBadge.textContent = `${res.data.available_slots} Available / ${res.data.total_slots} Total Slots`;
    }

    if (slots.length === 0) {
      slotsContainer.innerHTML = '<p style="grid-column: 1 / -1; color: var(--text-muted); text-align: center;">No time slots configured for this turf.</p>';
      return;
    }

    slotsContainer.innerHTML = slots.map(slot => {
      let cssClass = 'slot-btn';
      let statusText = 'Available';
      let disabledAttr = '';

      if (slot.status === 'AVAILABLE') {
        cssClass += ' available';
        statusText = 'Available';
      } else if (slot.status === 'BOOKED') {
        cssClass += ' booked';
        statusText = 'Booked';
        disabledAttr = 'disabled';
      } else {
        cssClass += ' disabled';
        statusText = 'Unavailable';
        disabledAttr = 'disabled';
      }

      return `
        <button 
          type="button" 
          class="${cssClass}" 
          id="slot-btn-${slot.id}" 
          ${disabledAttr}
          onclick="selectSlot(${slot.id}, '${slot.start_time}', '${slot.end_time}', '${slot.formatted}')"
        >
          <span class="slot-time">${slot.start_time} - ${slot.end_time}</span>
          <span class="slot-status-text">${statusText}</span>
        </button>
      `;
    }).join('');
  } else {
    slotsContainer.innerHTML = `<p style="grid-column: 1 / -1; color: var(--accent-red); text-align: center;">${res.message || 'Failed to load availability.'}</p>`;
  }
}

function selectSlot(slotId, startTime, endTime, formatted) {
  document.querySelectorAll('.slot-btn.selected').forEach(btn => {
    btn.classList.remove('selected');
    btn.classList.add('available');
    btn.querySelector('.slot-status-text').textContent = 'Available';
  });

  const btn = document.getElementById(`slot-btn-${slotId}`);
  if (btn) {
    btn.classList.remove('available');
    btn.classList.add('selected');
    btn.querySelector('.slot-status-text').textContent = 'Selected ✓';
  }

  selectedSlot = {
    id: slotId,
    start_time: startTime,
    end_time: endTime,
    formatted: formatted
  };

  updateBookingSummary();
}

function updateBookingSummary() {
  const summaryDate = document.getElementById('summary-date');
  const summarySlot = document.getElementById('summary-slot');
  const summarySport = document.getElementById('summary-sport');
  const summaryTotal = document.getElementById('summary-total-price');
  const summaryAddonsWrap = document.getElementById('summary-addons-list');
  const proceedBtn = document.getElementById('proceed-booking-btn');

  if (summaryDate) summaryDate.textContent = selectedDate ? formatDate(selectedDate) : 'Select a date';
  if (summarySlot) summarySlot.textContent = selectedSlot ? selectedSlot.formatted : 'Select a slot';
  if (summarySport) summarySport.textContent = selectedSport || 'Football';
  
  let addonCost = 0;
  selectedAddons.forEach(a => {
    if (a.includes('100')) addonCost += 100;
    if (a.includes('150')) addonCost += 150;
    if (a.includes('350')) addonCost += 350;
    if (a.includes('200')) addonCost += 200;
  });

  if (summaryAddonsWrap) {
    if (selectedAddons.length > 0) {
      summaryAddonsWrap.innerHTML = `
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-secondary);">
          <span>Gear & Extras:</span>
          <span style="color: var(--primary);">+₹${addonCost}</span>
        </div>
      `;
    } else {
      summaryAddonsWrap.innerHTML = '';
    }
  }

  if (summaryTotal && currentTurf) {
    summaryTotal.textContent = `₹${currentTurf.price_per_hour + addonCost}`;
  }

  if (proceedBtn) {
    proceedBtn.disabled = !(currentTurf && selectedDate && selectedSlot);
  }
}

function openBookingModal() {
  if (!Auth.isLoggedIn()) {
    Toast.warning('Please log in to complete your booking.');
    window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
    return;
  }

  if (!currentTurf || !selectedDate || !selectedSlot) {
    Toast.warning('Please select a date and time slot first.');
    return;
  }

  const user = Auth.getUser();

  let addonCost = 0;
  selectedAddons.forEach(a => {
    if (a.includes('100')) addonCost += 100;
    if (a.includes('150')) addonCost += 150;
    if (a.includes('350')) addonCost += 350;
    if (a.includes('200')) addonCost += 200;
  });

  document.getElementById('modal-turf-name').textContent = currentTurf.name;
  document.getElementById('modal-turf-location').textContent = currentTurf.location;
  document.getElementById('modal-booking-date').textContent = formatDate(selectedDate);
  document.getElementById('modal-booking-time').textContent = selectedSlot.formatted;
  document.getElementById('modal-booking-sport').textContent = selectedSport || 'Football';
  document.getElementById('modal-booking-price').textContent = `₹${currentTurf.price_per_hour + addonCost}`;
  document.getElementById('modal-user-name').textContent = user.name;
  document.getElementById('modal-user-email').textContent = user.email;

  const modalAddons = document.getElementById('modal-booking-addons');
  if (modalAddons) {
    modalAddons.textContent = selectedAddons.length > 0 ? selectedAddons.join(', ') : 'None';
  }

  openModal('booking-confirm-modal');
}

async function submitBooking() {
  const confirmBtn = document.getElementById('confirm-booking-btn');
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = 'Processing Reservation...';
  }

  const payload = {
    turf_id: currentTurf.id,
    slot_id: selectedSlot.id,
    booking_date: selectedDate,
    sport: selectedSport || 'Football',
    addons: selectedAddons
  };

  const res = await API.post('/bookings', payload);

  if (confirmBtn) {
    confirmBtn.disabled = false;
    confirmBtn.innerHTML = 'Confirm & Reserve';
  }

  if (res.ok && res.data && res.data.booking) {
    closeModal('booking-confirm-modal');
    
    // Show Success Modal
    const booking = res.data.booking;
    document.getElementById('success-booking-ref').textContent = booking.booking_reference;
    document.getElementById('success-turf-name').textContent = booking.turf_name;
    document.getElementById('success-date-time').textContent = `${formatDate(booking.booking_date)} (${booking.slot_time})`;
    document.getElementById('success-total-paid').textContent = `₹${booking.price}`;
    
    openModal('booking-success-modal');

    // Reset selection and refresh slots
    selectedSlot = null;
    updateBookingSummary();
    loadAvailability(currentTurf.id, selectedDate);
  } else {
    if (res.status === 409) {
      Toast.error('Conflict: This slot has already been reserved by another user. Please choose a different slot.');
      closeModal('booking-confirm-modal');
      selectedSlot = null;
      updateBookingSummary();
      loadAvailability(currentTurf.id, selectedDate);
    } else {
      Toast.error(res.message || 'Booking could not be created.');
    }
  }
}

// -------------------------------------------------------------
// REVIEWS ENGINE
// -------------------------------------------------------------
async function loadTurfReviews(turfId) {
  const container = document.getElementById('turf-reviews-list');
  if (!container) return;

  const res = await API.get(`/turfs/${turfId}/reviews`);
  if (res.ok && res.data) {
    const reviews = res.data.reviews || [];
    if (reviews.length === 0) {
      container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem;">No reviews yet. Be the first athlete to rate this facility!</p>';
      return;
    }

    container.innerHTML = reviews.map(r => `
      <div style="background: var(--bg-surface); padding: 1.25rem; border-radius: var(--radius-md); margin-bottom: 1rem; border: 1px solid var(--border-subtle);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <div style="width: 28px; height: 28px; border-radius: 50%; background: var(--primary-light); color: var(--primary); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700;">
              ${r.user_name ? r.user_name[0] : 'P'}
            </div>
            <strong style="color: var(--text-primary); font-size: 0.9rem;">${r.user_name}</strong>
          </div>
          <div style="color: #fbbf24; font-size: 0.9rem;">${'⭐'.repeat(r.rating)}</div>
        </div>
        <p style="color: var(--text-secondary); font-size: 0.875rem; line-height: 1.5; margin-bottom: 0.4rem;">${r.comment}</p>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${r.created_at ? r.created_at.split(' ')[0] : 'Verified Match Review'}</div>
      </div>
    `).join('');
  }
}

function setupReviewForm(turfId) {
  const form = document.getElementById('submit-review-form');
  const starsWrap = document.getElementById('star-picker');

  if (starsWrap) {
    const stars = starsWrap.querySelectorAll('span');
    stars.forEach(star => {
      star.addEventListener('click', () => {
        const val = parseInt(star.dataset.val);
        currentReviewRating = val;
        stars.forEach((s, idx) => {
          s.classList.toggle('active', idx < val);
        });
      });
    });
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!Auth.isLoggedIn()) {
        Toast.warning('Please log in to submit a review.');
        window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
        return;
      }

      const comment = document.getElementById('review-comment-input').value.trim();
      const btn = document.getElementById('submit-review-btn');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = 'Submitting...';
      }

      const res = await API.post(`/turfs/${turfId}/reviews`, {
        rating: currentReviewRating,
        comment: comment
      });

      if (btn) {
        btn.disabled = false;
        btn.innerHTML = 'Post Verified Review';
      }

      if (res.ok) {
        Toast.success('Review posted successfully!');
        form.reset();
        loadTurfReviews(turfId);
        if (res.data && res.data.turf_rating) {
          const ratingElem = document.getElementById('turf-rating');
          if (ratingElem) ratingElem.innerHTML = `⭐ ${res.data.turf_rating} <span>(${res.data.reviews_count} reviews)</span>`;
        }
      } else {
        Toast.error(res.message || 'Failed to submit review.');
      }
    });
  }
}
