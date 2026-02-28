/**
 * Auth.js — Login & Registration logic for CineMatch
 */

const API_BASE = window.location.origin;

// ─── Toast Notifications ───
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ─── Tab Switching ───
document.getElementById('loginTab').addEventListener('click', () => switchTab('login'));
document.getElementById('registerTab').addEventListener('click', () => switchTab('register'));

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.form-section').forEach(f => f.classList.remove('active'));

    if (tab === 'login') {
        document.getElementById('loginTab').classList.add('active');
        document.getElementById('loginForm').classList.add('active');
    } else {
        document.getElementById('registerTab').classList.add('active');
        document.getElementById('registerForm').classList.add('active');
    }
}

// ─── Register ───
document.getElementById('registerFormEl').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('registerBtn');
    btn.disabled = true;
    btn.textContent = 'Creating account...';

    const username = document.getElementById('regUsername').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;

    try {
        const res = await fetch(`${API_BASE}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password }),
        });
        const data = await res.json();

        if (res.ok) {
            showToast(data.message || 'Account created! Please log in.', 'success');
            switchTab('login');
            document.getElementById('loginUsername').value = username;
            document.getElementById('loginPassword').focus();
            document.getElementById('registerFormEl').reset();
        } else {
            showToast(data.detail || 'Registration failed', 'error');
        }
    } catch (err) {
        showToast('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create Account';
    }
});

// ─── Login ───
document.getElementById('loginFormEl').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('loginBtn');
    btn.disabled = true;
    btn.textContent = 'Signing in...';

    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    try {
        const res = await fetch(`${API_BASE}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        const data = await res.json();

        if (res.ok) {
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('username', data.username);
            showToast('Welcome back! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 600);
        } else {
            showToast(data.detail || 'Login failed', 'error');
        }
    } catch (err) {
        showToast('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sign In';
    }
});

// ─── Redirect if already logged in ───
(function checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        window.location.href = '/dashboard';
    }
})();
