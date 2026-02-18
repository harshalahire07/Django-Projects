const API_BASE = "/api";

function getHeaders() {
  const token = localStorage.getItem("access_token");
  return {
    "Content-Type": "application/json",
    Authorization: token ? `Bearer ${token}` : "",
  };
}

async function apiCall(endpoint, method = "GET", body = null) {
  const options = {
    method,
    headers: getHeaders(),
  };
  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, options);

    if (response.status === 401) {
      logout();
      return null;
    }

    if (response.status === 204) return true;

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || JSON.stringify(data));
    }

    return data;
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}

async function logout() {
  const refreshToken = localStorage.getItem("refresh_token");
  const accessToken = localStorage.getItem("access_token");

  if (refreshToken && accessToken) {
    try {
      await fetch(`${API_BASE}/accounts/logout/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });
    } catch (e) {
      console.error("Logout API failed", e);
    }
  }

  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login/";
}

function checkAuth() {
  if (!localStorage.getItem("access_token")) {
    window.location.href = "/login/";
  }
}

function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = message;
    el.style.display = "block";
  }
}

/* ============================================================
   TOAST NOTIFICATION SYSTEM
   ============================================================ */
const TOAST_ICONS = {
  success: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>`,
  error: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd"/></svg>`,
  warning: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 6a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 6zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/></svg>`,
  info: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clip-rule="evenodd"/></svg>`,
};

const TOAST_TITLES = {
  success: "Success",
  error: "Error",
  warning: "Warning",
  info: "Info",
};

function showToast(message, type = "info", duration = 4000) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-icon">${TOAST_ICONS[type] || TOAST_ICONS.info}</div>
    <div class="toast-body">
      <div class="toast-title">${TOAST_TITLES[type] || "Notice"}</div>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close" onclick="dismissToast(this.parentElement)">&times;</button>
    <div class="toast-progress" style="animation-duration: ${duration}ms;"></div>
  `;

  container.appendChild(toast);

  // Auto-dismiss
  const timer = setTimeout(() => dismissToast(toast), duration);
  toast._timer = timer;
}

function dismissToast(toast) {
  if (!toast || toast._dismissed) return;
  toast._dismissed = true;
  clearTimeout(toast._timer);
  toast.classList.add("toast-removing");
  toast.addEventListener("animationend", () => toast.remove());
}

/* ============================================================
   MODAL HELPERS
   ============================================================ */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "block";
    // Focus first input if exists
    const firstInput = modal.querySelector("input, textarea, select");
    if (firstInput) setTimeout(() => firstInput.focus(), 100);
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "none";
    // Clear inputs
    modal.querySelectorAll("input, textarea").forEach((el) => {
      el.value = "";
    });
  }
}

// Auto-bind overlay click-to-close on all modals
function initModals() {
  document.querySelectorAll(".modal-overlay").forEach((overlay) => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        overlay.style.display = "none";
        overlay.querySelectorAll("input, textarea").forEach((el) => {
          el.value = "";
        });
      }
    });
  });
}

/* ============================================================
   SIDEBAR MOBILE TOGGLE
   ============================================================ */
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (sidebar) {
    sidebar.classList.toggle("sidebar-open");
    if (backdrop) backdrop.classList.toggle("active");
  }
}

function closeSidebar() {
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (sidebar) {
    sidebar.classList.remove("sidebar-open");
    if (backdrop) backdrop.classList.remove("active");
  }
}

/* ============================================================
   INIT ON DOMCONTENTLOADED
   ============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  initModals();
});
