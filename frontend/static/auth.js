// ==========================================
// Authentication & Common API Utilities
// ==========================================

const API_BASE = "";

function getToken() {
  return localStorage.getItem("access_token");
}

function setToken(token) {
  localStorage.setItem("access_token", token);
}

function removeToken() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user_data");
}

function checkAuth() {
  const token = getToken();
  const isAuthPage = window.location.pathname.includes("login.html") || window.location.pathname.includes("signup.html");

  if (!token && !isAuthPage) {
    window.location.href = "/login.html";
  } else if (token && isAuthPage) {
    window.location.href = "/dashboard.html";
  }
}

function logout() {
  localStorage.clear();
  window.location.href = "/login.html";
}

async function fetchWithAuth(url, options = {}) {
  const token = getToken();
  const headers = {
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // If body is not FormData, add default json Content-Type if not set
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
      removeToken();
      window.location.href = "/login.html";
      throw new Error("Session expired. Please log in again.");
    }
    return response;
  } catch (err) {
    console.error("Fetch error:", err);
    throw err;
  }
}

function showToast(message, type = "info", duration = 4000) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  
  const icon = type === "success" ? "✓" : type === "error" ? "✕" : "ℹ";
  toast.innerHTML = `<span style="font-weight: bold;">${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Load logged-in user profile into sidebar
async function loadUserProfile() {
  try {
    const res = await fetchWithAuth("/auth/me");
    if (res.ok) {
      const user = await res.json();
      localStorage.setItem("user_data", JSON.stringify(user));
      
      const userNameEl = document.getElementById("sidebar-user-name");
      const userEmailEl = document.getElementById("sidebar-user-email");
      const userAvatarEl = document.getElementById("sidebar-user-avatar");

      if (userNameEl) userNameEl.textContent = user.name || "User";
      if (userEmailEl) userEmailEl.textContent = user.email || "";
      if (userAvatarEl && user.name) {
        userAvatarEl.textContent = user.name.charAt(0).toUpperCase();
      }
    }
  } catch (e) {
    console.warn("Could not load user profile", e);
  }
}

// Form Handlers
document.addEventListener("DOMContentLoaded", () => {
  // Login Form
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;
      const submitBtn = loginForm.querySelector("button[type=\"submit\"]");
      const errorAlert = document.getElementById("error-alert");

      if (errorAlert) errorAlert.style.display = "none";
      submitBtn.disabled = true;
      submitBtn.textContent = "Signing in...";

      try {
        const response = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        if (response.ok && data.access_token) {
          setToken(data.access_token);
          showToast("Sign in successful! Redirecting...", "success");
          setTimeout(() => {
            window.location.href = "/dashboard.html";
          }, 600);
        } else {
          if (errorAlert) {
            errorAlert.textContent = data.detail || "Login failed. Please check your credentials.";
            errorAlert.style.display = "block";
          } else {
            showToast(data.detail || "Login failed.", "error");
          }
        }
      } catch (err) {
        if (errorAlert) {
          errorAlert.textContent = "Server connection error. Please try again.";
          errorAlert.style.display = "block";
        }
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Sign In";
      }
    });
  }

  // Signup Form
  const signupForm = document.getElementById("signup-form");
  if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("name").value.trim();
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;
      const confirmPassword = document.getElementById("confirm_password").value;
      const submitBtn = signupForm.querySelector("button[type=\"submit\"]");
      const errorAlert = document.getElementById("error-alert");

      if (errorAlert) errorAlert.style.display = "none";

      if (password !== confirmPassword) {
        if (errorAlert) {
          errorAlert.textContent = "Passwords do not match.";
          errorAlert.style.display = "block";
        }
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = "Creating account...";

      try {
        const response = await fetch("/auth/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name,
            email,
            password,
            confirm_password: confirmPassword
          })
        });

        const data = await response.json();
        if (response.ok) {
          showToast("Account created successfully! Signing you in...", "success");
          // Auto login
          const loginRes = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
          });
          const loginData = await loginRes.json();
          if (loginRes.ok && loginData.access_token) {
            setToken(loginData.access_token);
            setTimeout(() => {
              window.location.href = "/dashboard.html";
            }, 800);
          } else {
            window.location.href = "/login.html";
          }
        } else {
          let errorMsg = data.detail;
          if (Array.isArray(data.detail)) {
            errorMsg = data.detail.map(d => d.msg || JSON.stringify(d)).join(", ");
          }
          if (errorAlert) {
            errorAlert.textContent = errorMsg || "Signup failed.";
            errorAlert.style.display = "block";
          }
        }
      } catch (err) {
        if (errorAlert) {
          errorAlert.textContent = "Connection error. Please try again.";
          errorAlert.style.display = "block";
        }
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Create Account";
      }
    });
  }

  // Load user profile on protected pages
  if (getToken() && !window.location.pathname.includes("login.html") && !window.location.pathname.includes("signup.html")) {
    loadUserProfile();
  }
});
