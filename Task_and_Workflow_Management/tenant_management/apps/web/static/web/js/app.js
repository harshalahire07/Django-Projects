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
      // Token expired or invalid
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
