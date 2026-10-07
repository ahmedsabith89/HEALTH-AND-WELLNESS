// Global App State & Utility Framework
const State = {
  currentUser: null,
  currentTab: 'overview',
  refreshInterval: null
};

// API Fetch Wrapper
async function api(endpoint, options = {}) {
  const headers = options.headers || {};
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  
  const token = localStorage.getItem('hub_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers
  };

  try {
    const res = await fetch(endpoint, config);
    if (res.status === 401) {
      if (State.currentUser) {
        logout(false);
      }
      throw new Error('Authentication required');
    }
    
    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(errData.detail || `Server error (${res.status})`);
    }

    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await res.json();
    }
    return res;
  } catch (err) {
    console.error('API Error:', err);
    throw err;
  }
}

// Toast Notifications
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : type === 'error' ? '⚠️' : 'ℹ️'}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// Authentication Actions
async function checkAuth() {
  try {
    const data = await api('/api/auth/me');
    State.currentUser = data;
    renderApp();
  } catch (err) {
    State.currentUser = null;
    renderLogin();
  }
}

async function loginUser(admissionNumber, password) {
  try {
    const res = await api('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ admission_number: admissionNumber, password })
    });
    localStorage.setItem('hub_token', res.token);
    State.currentUser = res.user;
    showToast(`Welcome, ${res.user.full_name}!`, 'success');
    renderApp();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function logout(promptUser = true) {
  try {
    await api('/api/auth/logout', { method: 'POST' });
  } catch (e) {}
  localStorage.removeItem('hub_token');
  State.currentUser = null;
  if (promptUser) showToast('Logged out successfully', 'info');
  renderLogin();
}

// Render Top-Level App
function renderApp() {
  const root = document.getElementById('appRoot');
  if (!State.currentUser) {
    renderLogin();
    return;
  }

  // Update Nav
  const navUser = document.getElementById('navUser');
  if (navUser) {
    const role = State.currentUser.role;
    let badgeClass = 'badge-neutral';
    if (role === 'ADMIN') badgeClass = 'badge-primary';
    else if (role === 'TESTER') badgeClass = 'badge-tester';
    else if (role === 'STUDENT') badgeClass = 'badge-accent';

    navUser.innerHTML = `
      <div class="user-pill">
        <span>${role === 'ADMIN' ? '👑' : role === 'TESTER' ? '🔍' : '🎓'}</span>
        <span>${State.currentUser.full_name}</span>
        <span class="badge ${badgeClass}">${role}</span>
      </div>
      <button class="btn btn-secondary btn-sm" onclick="logout()">Logout</button>
    `;
  }

  if (State.currentUser.role === 'ADMIN') {
    renderAdminView();
  } else if (State.currentUser.role === 'TESTER') {
    renderTesterView();
  } else {
    renderStudentView();
  }
}

// Render Login Interface
function renderLogin() {
  const navUser = document.getElementById('navUser');
  if (navUser) navUser.innerHTML = '';

  const root = document.getElementById('appRoot');
  root.innerHTML = `
    <div style="max-width: 480px; margin: 2rem auto;">
      <div class="card" style="padding: 2.25rem; border: 1px solid rgba(16, 185, 129, 0.25); box-shadow: 0 12px 30px rgba(5, 150, 105, 0.12);">
        <div style="text-align: center; margin-bottom: 1.75rem;">
          <div class="brand-icon-wrapper" style="width: 58px; height: 58px; margin: 0 auto 0.85rem auto; font-size: 1.85rem;">
            <span>🌿</span>
            <div class="brand-pulse"></div>
          </div>
          <h2 style="font-size: 1.45rem; font-weight: 900; color: #065f46; letter-spacing: -0.02em;">
            HEALTH AND WELLNESS - PRESENTATION
          </h2>
          <p style="font-size: 0.825rem; color: var(--text-muted); margin-top: 0.35rem; font-weight: 500;">
            Private College-Class Presentation System • 69 Students • 10 Teams
          </p>
        </div>

        <form id="loginForm" onsubmit="handleLoginSubmit(event)">
          <div class="form-group">
            <label class="form-label">Admission Number, Username, or Email</label>
            <input type="text" id="loginAdm" class="form-control" placeholder="e.g. ADM2026001, ahmed, or TESTER01" required autofocus />
          </div>

          <div class="form-group">
            <label class="form-label">Password</label>
            <input type="password" id="loginPwd" class="form-control" placeholder="Enter your password" required />
          </div>

          <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem; padding: 0.75rem;">
            Log In to Presentation Hub
          </button>
        </form>

        <div style="margin-top: 1.75rem; padding-top: 1.5rem; border-top: 1px solid var(--border); font-size: 0.82rem;">
          <div style="font-weight: 800; color: #065f46; margin-bottom: 0.65rem; text-transform: uppercase; letter-spacing: 0.04em; display: flex; align-items: center; gap: 0.4rem;">
            <span>⚡</span> Quick-Switch Evaluation Logins
          </div>

          <!-- Admin Section -->
          <div style="margin-bottom: 0.75rem;">
            <div style="font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.3rem;">
              Course Administrator (Ahmed Sabith)
            </div>
            <button class="btn btn-secondary btn-sm" style="width: 100%; justify-content: flex-start;" onclick="fillLogin('ADMIN', 'admin123')">
              👑 <strong>Ahmed Sabith</strong> (Coordinator) <span style="margin-left: auto; color: var(--text-muted); font-size: 0.75rem;">ADMIN / admin123</span>
            </button>
          </div>

          <!-- Tester Profiles Section (Non-student evaluators) -->
          <div style="margin-bottom: 0.75rem;">
            <div style="font-size: 0.72rem; font-weight: 800; color: #6d28d9; text-transform: uppercase; margin-bottom: 0.3rem; display: flex; justify-content: space-between;">
              <span>Independent Testers (Excluded from Groups)</span>
              <span class="badge badge-tester" style="padding: 0.1rem 0.4rem; font-size: 0.68rem;">QA Only</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 0.35rem;">
              <button class="btn btn-secondary btn-sm" style="justify-content: flex-start;" onclick="fillLogin('TESTER01', 'tester123')">
                🔍 <strong>Dr. Evelyn Reed</strong> (QA Evaluator) <span style="margin-left: auto; color: var(--text-muted); font-size: 0.75rem;">TESTER01</span>
              </button>
              <button class="btn btn-secondary btn-sm" style="justify-content: flex-start;" onclick="fillLogin('TESTER02', 'tester123')">
                🔍 <strong>Marcus Chen</strong> (Wellness Auditor) <span style="margin-left: auto; color: var(--text-muted); font-size: 0.75rem;">TESTER02</span>
              </button>
              <button class="btn btn-secondary btn-sm" style="justify-content: flex-start;" onclick="fillLogin('TESTER03', 'tester123')">
                🔍 <strong>Aria Sharma</strong> (UX Reviewer) <span style="margin-left: auto; color: var(--text-muted); font-size: 0.75rem;">TESTER03</span>
              </button>
            </div>
          </div>

          <!-- Sample Students Section (69 Group Members) -->
          <div>
            <div style="font-size: 0.72rem; font-weight: 800; color: #0284c7; text-transform: uppercase; margin-bottom: 0.3rem;">
              Enrolled Students (Class Roster of 69)
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem;">
              <button class="btn btn-secondary btn-sm" onclick="fillLogin('ADM2026001', 'student123')">
                🎓 Student 001
              </button>
              <button class="btn btn-secondary btn-sm" onclick="fillLogin('ADM2026007', 'student123')">
                🎓 Student 007
              </button>
              <button class="btn btn-secondary btn-sm" onclick="fillLogin('ADM2026014', 'student123')">
                🎓 Student 014
              </button>
              <button class="btn btn-secondary btn-sm" onclick="fillLogin('ADM2026069', 'student123')">
                🎓 Student 069 (6-member)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function fillLogin(adm, pwd) {
  document.getElementById('loginAdm').value = adm;
  document.getElementById('loginPwd').value = pwd;
  loginUser(adm, pwd);
}

function handleLoginSubmit(e) {
  e.preventDefault();
  const adm = document.getElementById('loginAdm').value.trim();
  const pwd = document.getElementById('loginPwd').value.trim();
  loginUser(adm, pwd);
}

// Modal helper
function openModal(htmlContent) {
  closeModal();
  const modal = document.createElement('div');
  modal.id = 'activeModal';
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal-content" onclick="event.stopPropagation()">
      ${htmlContent}
    </div>
  `;
  modal.onclick = closeModal;
  document.body.appendChild(modal);
}

function closeModal() {
  const modal = document.getElementById('activeModal');
  if (modal) modal.remove();
}

window.addEventListener('DOMContentLoaded', () => {
  checkAuth();
});
