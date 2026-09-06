/**
 * User Profile & Account Settings Logic
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;

  const res = await API.get('/auth/me');
  if (res.ok && res.data && res.data.user) {
    const user = res.data.user;
    
    // Update local storage in case info updated
    localStorage.setItem('turfzone_user', JSON.stringify(user));

    document.getElementById('profile-display-name').textContent = user.name;
    document.getElementById('profile-display-email').textContent = user.email;
    document.getElementById('profile-display-phone').textContent = user.phone;
    document.getElementById('profile-display-role').textContent = user.role;
    document.getElementById('profile-display-joined').textContent = user.created_at ? user.created_at.split(' ')[0] : 'Recently';

    // Pre-fill Edit form
    const nameInput = document.getElementById('edit-profile-name');
    const phoneInput = document.getElementById('edit-profile-phone');
    if (nameInput) nameInput.value = user.name;
    if (phoneInput) phoneInput.value = user.phone;
  }

  // Load user booking stats for profile
  const bookingsRes = await API.get('/bookings');
  if (bookingsRes.ok && bookingsRes.data) {
    const count = (bookingsRes.data.bookings || []).length;
    const countElem = document.getElementById('profile-booking-count');
    if (countElem) countElem.textContent = count;
  }

  // Handle Profile Update Form
  const profileForm = document.getElementById('edit-profile-form');
  if (profileForm) {
    profileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('edit-profile-name').value.trim();
      const phone = document.getElementById('edit-profile-phone').value.trim();

      const btn = document.getElementById('save-profile-btn');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = 'Saving...';
      }

      const updateRes = await API.put('/auth/profile', { name, phone });

      if (btn) {
        btn.disabled = false;
        btn.innerHTML = 'Save Profile Changes';
      }

      if (updateRes.ok && updateRes.data && updateRes.data.user) {
        Auth.setSession(Auth.getToken(), updateRes.data.user);
        Toast.success('Profile updated successfully!');
        setTimeout(() => location.reload(), 1000);
      } else {
        Toast.error(updateRes.message || 'Failed to update profile.');
      }
    });
  }

  // Handle Password Change Form
  const passwordForm = document.getElementById('change-password-form');
  if (passwordForm) {
    passwordForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const currentPassword = document.getElementById('current-password').value;
      const newPassword = document.getElementById('new-password').value;
      const confirmNewPassword = document.getElementById('confirm-new-password').value;

      if (newPassword !== confirmNewPassword) {
        Toast.error('New passwords do not match.');
        return;
      }

      const btn = document.getElementById('save-password-btn');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = 'Updating Password...';
      }

      const pwRes = await API.put('/auth/profile', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_new_password: confirmNewPassword
      });

      if (btn) {
        btn.disabled = false;
        btn.innerHTML = 'Update Password';
      }

      if (pwRes.ok) {
        Toast.success('Password changed successfully!');
        passwordForm.reset();
      } else {
        Toast.error(pwRes.message || 'Failed to change password.');
      }
    });
  }
});
