// Lógica da página de login/cadastro.

if (Auth.isLoggedIn()) {
  window.location.href = "dashboard.html";
}

const tabLogin = document.getElementById("tab-login");
const tabRegister = document.getElementById("tab-register");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const alertBox = document.getElementById("alert-box");

function switchTab(tab) {
  alertBox.innerHTML = "";
  const isLogin = tab === "login";
  tabLogin.classList.toggle("active", isLogin);
  tabRegister.classList.toggle("active", !isLogin);
  loginForm.classList.toggle("hidden", !isLogin);
  registerForm.classList.toggle("hidden", isLogin);
}

tabLogin.addEventListener("click", () => switchTab("login"));
tabRegister.addEventListener("click", () => switchTab("register"));

function renderAlert(message, type = "error") {
  alertBox.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
}

async function afterLoginSuccess(token) {
  Auth.setToken(token);
  try {
    const user = await Api.me();
    Auth.setUser(user);
    window.location.href = user.role === "admin" ? "admin.html" : "dashboard.html";
  } catch (error) {
    renderAlert("Login realizado, mas não foi possível carregar o perfil.");
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const submitBtn = loginForm.querySelector("button[type=submit]");

  submitBtn.disabled = true;
  try {
    const { access_token } = await Api.login({ email, password });
    await afterLoginSuccess(access_token);
  } catch (error) {
    renderAlert(error.message || "Não foi possível entrar.");
  } finally {
    submitBtn.disabled = false;
  }
});

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = document.getElementById("register-name").value.trim();
  const email = document.getElementById("register-email").value.trim();
  const password = document.getElementById("register-password").value;
  const submitBtn = registerForm.querySelector("button[type=submit]");

  submitBtn.disabled = true;
  try {
    await Api.register({ name, email, password });
    const { access_token } = await Api.login({ email, password });
    await afterLoginSuccess(access_token);
  } catch (error) {
    renderAlert(error.message || "Não foi possível criar a conta.");
  } finally {
    submitBtn.disabled = false;
  }
});
