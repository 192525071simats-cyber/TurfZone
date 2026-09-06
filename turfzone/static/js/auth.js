/**
 * TurfZone Authentication & Dynamic Navigation
 */

const Auth = {
  getUser() {
    try {
      const userStr = localStorage.getItem('turfzone_user');
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  },

  getToken() {
    return localStorage.getItem('turfzone_token');
  },

  isLoggedIn() {
    return !!this.getToken() && !!this.getUser();
  },

  isAdmin() {
    const user = this.getUser();
    return user && user.role === 'ADMIN';
  },

  setSession(token, user) {
    localStorage.setItem('turfzone_token', token);
    localStorage.setItem('turfzone_user', JSON.stringify(user));
    this.updateNavbar();
  },

  async login(email, password) {
    const res = await API.post('/auth/login', { email, password });
    if (res.ok && res.data) {
      this.setSession(res.data.token, res.data.user);
      Toast.success(res.message || 'Welcome back!');
      return { success: true, user: res.data.user };
    } else {
      Toast.error(res.message || 'Login failed.');
      return { success: false, message: res.message };
    }
  },

  async register(payload) {
    const res = await API.post('/auth/register', payload);
    if (res.ok) {
      Toast.success(res.message || 'Account created! Please log in.');
      return { success: true };
    } else {
      Toast.error(res.message || 'Registration failed.');
      return { success: false, message: res.message };
    }
  },

  logout() {
    localStorage.removeItem('turfzone_token');
    localStorage.removeItem('turfzone_user');
    Toast.info('You have been logged out.');
    this.updateNavbar();
    setTimeout(() => {
      window.location.href = '/login';
    }, 500);
  },

  updateNavbar() {
    const navLinksContainer = document.getElementById('navbar-links');
    const navActionsContainer = document.getElementById('navbar-actions');
    if (!navLinksContainer || !navActionsContainer) return;

    const currentPath = window.location.pathname;
    const user = this.getUser();
    const loggedIn = this.isLoggedIn();
    const admin = this.isAdmin();

    let linksHtml = '';
    let actionsHtml = '';

    if (admin) {
      // Admin Navigation
      linksHtml = `
        <li><a href="/" class="nav-link ${currentPath === '/' ? 'active' : ''}">Home</a></li>
        <li><a href="/admin" class="nav-link ${currentPath === '/admin' ? 'active' : ''}">Admin Control</a></li>
        <li><a href="/turfs" class="nav-link ${currentPath === '/turfs' ? 'active' : ''}">Turfs</a></li>
        <li><a href="/tournaments" class="nav-link ${currentPath === '/tournaments' ? 'active' : ''}">Tournaments</a></li>
        <li><a href="/turf-bot" class="nav-link ${currentPath === '/turf-bot' ? 'active' : ''}">Turf-Bot</a></li>
      `;
      actionsHtml = `
        <div style="display: flex; align-items: center; gap: 0.8rem;">
          <span class="badge badge-amber" style="padding: 0.35rem 0.75rem;">🛡️ Admin</span>
          <button onclick="Auth.logout()" class="btn btn-secondary btn-sm">Logout</button>
        </div>
      `;
    } else if (loggedIn) {
      // Logged-in User Navigation
      linksHtml = `
        <li><a href="/" class="nav-link ${currentPath === '/' ? 'active' : ''}">Home</a></li>
        <li><a href="/turfs" class="nav-link ${currentPath === '/turfs' ? 'active' : ''}">Explore Turfs</a></li>
        <li><a href="/tournaments" class="nav-link ${currentPath === '/tournaments' ? 'active' : ''}">Tournaments</a></li>
        <li><a href="/dashboard" class="nav-link ${currentPath === '/dashboard' ? 'active' : ''}">Dashboard</a></li>
        <li><a href="/bookings" class="nav-link ${currentPath === '/bookings' ? 'active' : ''}">My Bookings</a></li>
        <li><a href="/turf-bot" class="nav-link ${currentPath === '/turf-bot' ? 'active' : ''}">Turf-Bot</a></li>
      `;
      actionsHtml = `
        <div style="display: flex; align-items: center; gap: 0.8rem;">
          <a href="/profile" class="btn btn-secondary btn-sm" style="display: flex; align-items: center; gap: 0.4rem;">
            👤 <span>${user.name.split(' ')[0]}</span>
          </a>
          <button onclick="Auth.logout()" class="btn btn-outline btn-sm">Logout</button>
        </div>
      `;
    } else {
      // Public / Guest Navigation
      linksHtml = `
        <li><a href="/" class="nav-link ${currentPath === '/' ? 'active' : ''}">Home</a></li>
        <li><a href="/turfs" class="nav-link ${currentPath === '/turfs' ? 'active' : ''}">Explore Turfs</a></li>
        <li><a href="/tournaments" class="nav-link ${currentPath === '/tournaments' ? 'active' : ''}">Tournaments</a></li>
        <li><a href="/turf-bot" class="nav-link ${currentPath === '/turf-bot' ? 'active' : ''}">Turf-Bot</a></li>
      `;
      actionsHtml = `
        <a href="/login" class="btn btn-secondary btn-sm">Login</a>
        <a href="/register" class="btn btn-primary btn-sm">Register</a>
      `;
    }

    navLinksContainer.innerHTML = linksHtml;
    navActionsContainer.innerHTML = actionsHtml;
  },

  requireAuth() {
    if (!this.isLoggedIn()) {
      Toast.warning('Please log in to access this page.');
      window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
      return false;
    }
    return true;
  },

  requireAdmin() {
    if (!this.isLoggedIn() || !this.isAdmin()) {
      Toast.error('Access restricted. Admin authorization required.');
      window.location.href = '/login';
      return false;
    }
    return true;
  }
};

document.addEventListener('DOMContentLoaded', () => {
  Auth.updateNavbar();
});
