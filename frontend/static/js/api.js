const API = {
  getToken: () => localStorage.getItem('store_token'),
  getUsername: () => localStorage.getItem('store_username'),
  
  setAuth: (token, username) => {
    localStorage.setItem('store_token', token);
    localStorage.setItem('store_username', username);
    API.renderUserNav();
  },

  clearAuth: () => {
    localStorage.removeItem('store_token');
    localStorage.removeItem('store_username');
    API.renderUserNav();
  },

  authFetch: async (url, options = {}) => {
    options.headers = options.headers || {};
    const token = API.getToken();
    if (token) {
      options.headers['Authorization'] = `Bearer ${token}`;
    }
    return fetch(url, options);
  },

  renderUserNav: () => {
    const navActions = document.querySelector('.nav-actions');
    if (!navActions) return;

    const username = API.getUsername();
    const existingUserEl = document.getElementById('user-nav-block');
    if (existingUserEl) existingUserEl.remove();

    const userBlock = document.createElement('div');
    userBlock.id = 'user-nav-block';
    userBlock.style.display = 'flex';
    userBlock.style.alignItems = 'center';
    userBlock.style.gap = '1rem';

    if (username) {
      userBlock.innerHTML = `
        <span class="nav-link">
          Hi, <strong style="color: var(--accent-primary);">${username}</strong>
        </span>
        <button id="logout-btn" class="nav-link" style="background:none; border:none; cursor:pointer; font-family:inherit;">Logout</button>
      `;
    } else {
      userBlock.innerHTML = `
        <a href="/login" class="nav-link">Sign In</a>
        <a href="/register" class="btn btn-secondary btn-sm">Register</a>
      `;
    }

    navActions.insertBefore(userBlock, navActions.firstChild);

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        API.clearAuth();
        showToast('Logged out successfully');
        setTimeout(() => window.location.href = '/', 500);
      });
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  API.renderUserNav();
  API.fetchCartBadge();
});

API.fetchCartBadge = async () => {
  try {
    const res = await API.authFetch('/api/cart');
    if (res.ok) {
      const data = await res.json();
      const badge = document.getElementById('cart-badge');
      if (badge) badge.textContent = data.total_count || 0;
    }
  } catch (e) {
    console.error('Error loading cart badge:', e);
  }
};
