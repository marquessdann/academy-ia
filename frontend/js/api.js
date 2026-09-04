// Camada única de comunicação com a API do GymFlow AI.
// Ajuste API_BASE_URL se o backend estiver rodando em outro host/porta.
const API_BASE_URL = window.GYMFLOW_API_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "gymflow_token";
const USER_KEY = "gymflow_user";

const Auth = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  getUser: () => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  setUser: (user) => localStorage.setItem(USER_KEY, JSON.stringify(user)),
  isLoggedIn: () => Boolean(localStorage.getItem(TOKEN_KEY)),
};

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function apiRequest(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = Auth.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (networkError) {
    throw new ApiError("Não foi possível conectar à API. Verifique se o backend está rodando.", 0);
  }

  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data && data.detail ? data.detail : "Erro inesperado";
    const message = Array.isArray(detail) ? detail.map((d) => d.msg).join(", ") : detail;
    throw new ApiError(message, response.status);
  }

  return data;
}

const Api = {
  register: (payload) => apiRequest("/auth/register", { method: "POST", body: payload, auth: false }),
  login: (payload) => apiRequest("/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => apiRequest("/users/me"),

  listCategories: () => apiRequest("/categories", { auth: false }),
  createCategory: (payload) => apiRequest("/categories", { method: "POST", body: payload }),

  listInstructors: () => apiRequest("/instructors", { auth: false }),
  createInstructor: (payload) => apiRequest("/instructors", { method: "POST", body: payload }),

  listClasses: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/classes${query ? `?${query}` : ""}`, { auth: false });
  },
  createClass: (payload) => apiRequest("/classes", { method: "POST", body: payload }),

  createBooking: (classId) => apiRequest("/bookings", { method: "POST", body: { class_id: classId } }),
  cancelBooking: (bookingId) => apiRequest(`/bookings/${bookingId}`, { method: "DELETE" }),
  myBookings: () => apiRequest("/users/me/bookings"),

  occupancyReport: () => apiRequest("/analytics/occupancy"),
  quietestTimes: () => apiRequest("/analytics/quietest-times"),
  recommendations: () => apiRequest("/analytics/recommendations"),

  chat: (message) => apiRequest("/ai/chat", { method: "POST", body: { message } }),
};

function requireAuth() {
  if (!Auth.isLoggedIn()) {
    window.location.href = "index.html";
  }
}

function requireAdmin() {
  requireAuth();
  const user = Auth.getUser();
  if (!user || user.role !== "admin") {
    window.location.href = "dashboard.html";
  }
}

function showToast(message, type = "success") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function formatDateTime(isoString) {
  const date = new Date(isoString);
  return date.toLocaleString("pt-BR", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function initials(name) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}
