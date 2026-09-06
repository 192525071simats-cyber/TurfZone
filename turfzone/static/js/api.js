/**
 * TurfZone API & Toast Utilities
 */

const API_BASE = '/api';

// Toast Notification Manager
const Toast = {
  container: null,

  init() {
    if (!this.container) {
      this.container = document.getElementById('toast-container');
      if (!this.container) {
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        document.body.appendChild(this.container);
      }
    }
  },

  show(message, type = 'info', duration = 4000) {
    this.init();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'warning') icon = '⚠️';

    toast.innerHTML = `
      <div class="toast-icon">${icon}</div>
      <div class="toast-body">${message}</div>
    `;

    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  success(msg) { this.show(msg, 'success'); },
  error(msg) { this.show(msg, 'error'); },
  warning(msg) { this.show(msg, 'warning'); },
  info(msg) { this.show(msg, 'info'); }
};

// API Fetch Client
const API = {
  getToken() {
    return localStorage.getItem('turfzone_token');
  },

  getHeaders(customHeaders = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...customHeaders
    };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  },

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http')
      ? endpoint
      : (endpoint.startsWith(API_BASE) ? endpoint : `${API_BASE}${endpoint}`);
    options.headers = this.getHeaders(options.headers);

    try {
      const res = await fetch(url, options);
      const data = await res.json().catch(() => ({
        success: false,
        message: 'Invalid response from server',
        error: 'JSON_PARSE_ERROR'
      }));

      if (!res.ok) {
        // Handle 401 Unauthorized
        if (res.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register')) {
          localStorage.removeItem('turfzone_token');
          localStorage.removeItem('turfzone_user');
          if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
            Toast.warning('Session expired. Please log in again.');
            setTimeout(() => { window.location.href = '/login'; }, 1500);
          }
        }
        return { ok: false, status: res.status, ...data };
      }

      return { ok: true, status: res.status, ...data };
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      return {
        ok: false,
        success: false,
        status: 0,
        message: 'Unable to connect to TurfZone server. Please check your connection.',
        error: 'NETWORK_ERROR'
      };
    }
  },

  get(endpoint, params = {}) {
    let url = endpoint;
    const queryString = new URLSearchParams(params).toString();
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString;
    }
    return this.request(url, { method: 'GET' });
  },

  post(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },

  put(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body)
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
};
