requireAuth();

const user = Auth.getUser();
document.getElementById("user-name").textContent = user?.name || "Aluno";
document.getElementById("user-role").textContent = user?.role || "student";
document.getElementById("user-avatar").textContent = user ? initials(user.name) : "--";

document.getElementById("logout-btn").addEventListener("click", () => {
  Auth.clear();
  window.location.href = "index.html";
});

// ---------- Navegação entre seções ----------
const navLinks = document.querySelectorAll(".nav-link");
const views = {
  classes: document.getElementById("view-classes"),
  bookings: document.getElementById("view-bookings"),
  chat: document.getElementById("view-chat"),
};

navLinks.forEach((link) => {
  link.addEventListener("click", () => {
    navLinks.forEach((l) => l.classList.remove("active"));
    link.classList.add("active");
    Object.entries(views).forEach(([key, section]) => section.classList.toggle("hidden", key !== link.dataset.view));

    if (link.dataset.view === "bookings") loadBookings();
  });
});

// ---------- Aulas disponíveis ----------
const classesContainer = document.getElementById("classes-container");
const categorySelect = document.getElementById("filter-category");

function spotsBarClass(availableSpots, capacity) {
  if (availableSpots <= 0) return "full";
  if (availableSpots / capacity <= 0.25) return "warn";
  return "";
}

function renderClassCard(gymClass) {
  const occupiedRatio = (gymClass.booked_count / gymClass.capacity) * 100;
  const barClass = spotsBarClass(gymClass.available_spots, gymClass.capacity);

  const card = document.createElement("div");
  card.className = "card class-card";
  card.innerHTML = `
    <div class="top-row">
      <span class="category-badge">${gymClass.category.name}</span>
      ${gymClass.is_full ? '<span class="badge badge-full">Lotada</span>' : ""}
    </div>
    <h3>${gymClass.title}</h3>
    <div class="meta">
      <span>🗓️ ${formatDateTime(gymClass.start_time)}</span>
      <span>🧑‍🏫 ${gymClass.instructor.name}</span>
    </div>
    <div class="spots-indicator">
      <div class="spots-bar"><div class="spots-bar-fill ${barClass}" style="width:${Math.min(occupiedRatio, 100)}%"></div></div>
      <span class="spots-label">${gymClass.available_spots}/${gymClass.capacity} vagas</span>
    </div>
    <button class="btn ${gymClass.is_full ? "btn-secondary" : "btn-primary"} btn-block" ${gymClass.is_full ? "disabled" : ""}>
      ${gymClass.is_full ? "Sem vagas" : "Reservar"}
    </button>
  `;

  const button = card.querySelector("button");
  if (!gymClass.is_full) {
    button.addEventListener("click", async () => {
      button.disabled = true;
      button.textContent = "Reservando...";
      try {
        await Api.createBooking(gymClass.id);
        showToast("Reserva confirmada!", "success");
        loadClasses();
      } catch (error) {
        showToast(error.message, "error");
        button.disabled = false;
        button.textContent = "Reservar";
      }
    });
  }

  return card;
}

async function loadCategories() {
  try {
    const categories = await Api.listCategories();
    categories.forEach((category) => {
      const option = document.createElement("option");
      option.value = category.id;
      option.textContent = category.name;
      categorySelect.appendChild(option);
    });
  } catch (error) {
    // silencioso: filtro de categoria é acessório
  }
}

async function loadClasses() {
  classesContainer.innerHTML = '<div class="loading">Carregando aulas...</div>';
  try {
    const params = {};
    if (categorySelect.value) params.category_id = categorySelect.value;
    const classes = await Api.listClasses(params);

    if (classes.length === 0) {
      classesContainer.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="icon">🗓️</div>
          <p>Nenhuma aula encontrada para este filtro.</p>
        </div>`;
      return;
    }

    classesContainer.innerHTML = "";
    classes
      .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
      .forEach((gymClass) => classesContainer.appendChild(renderClassCard(gymClass)));
  } catch (error) {
    classesContainer.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">⚠️ ${error.message}</div>`;
  }
}

categorySelect.addEventListener("change", loadClasses);

// ---------- Minhas reservas ----------
const bookingsContainer = document.getElementById("bookings-container");

function renderBookingItem(booking) {
  const item = document.createElement("div");
  item.className = "list-item";
  const badgeClass = booking.status === "confirmed" ? "badge-confirmed" : "badge-cancelled";
  const statusLabel = booking.status === "confirmed" ? "Confirmada" : "Cancelada";

  item.innerHTML = `
    <div class="info">
      <h4>${booking.gym_class.title} <span class="badge ${badgeClass}">${statusLabel}</span></h4>
      <p>${formatDateTime(booking.gym_class.start_time)} · ${booking.gym_class.category.name} · ${booking.gym_class.instructor.name}</p>
    </div>
  `;

  if (booking.status === "confirmed") {
    const cancelBtn = document.createElement("button");
    cancelBtn.className = "btn btn-danger btn-sm";
    cancelBtn.textContent = "Cancelar";
    cancelBtn.addEventListener("click", async () => {
      cancelBtn.disabled = true;
      try {
        await Api.cancelBooking(booking.id);
        showToast("Reserva cancelada.", "success");
        loadBookings();
      } catch (error) {
        showToast(error.message, "error");
        cancelBtn.disabled = false;
      }
    });
    item.appendChild(cancelBtn);
  }

  return item;
}

async function loadBookings() {
  bookingsContainer.innerHTML = '<div class="loading">Carregando reservas...</div>';
  try {
    const bookings = await Api.myBookings();
    if (bookings.length === 0) {
      bookingsContainer.innerHTML = `
        <div class="empty-state">
          <div class="icon">🎟️</div>
          <p>Você ainda não fez nenhuma reserva.</p>
        </div>`;
      return;
    }
    bookingsContainer.innerHTML = "";
    bookings
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .forEach((booking) => bookingsContainer.appendChild(renderBookingItem(booking)));
  } catch (error) {
    bookingsContainer.innerHTML = `<div class="empty-state">⚠️ ${error.message}</div>`;
  }
}

// ---------- Chat IA ----------
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");

function appendMessage(role, text, toolsUsed = []) {
  const msg = document.createElement("div");
  msg.className = `msg ${role}`;
  const avatarLabel = role === "user" ? initials(user?.name || "Você") : "IA";
  const toolsLine = toolsUsed.length ? `<div class="tools-used">🔧 tools: ${toolsUsed.join(", ")}</div>` : "";
  msg.innerHTML = `
    <div class="avatar">${avatarLabel}</div>
    <div>
      <div class="bubble">${text}</div>
      ${toolsLine}
    </div>
  `;
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage(text) {
  appendMessage("user", text);
  chatInput.value = "";
  const typingId = "typing-indicator";
  appendMessage("assistant", "Digitando...");
  chatMessages.lastElementChild.id = typingId;

  try {
    const response = await Api.chat(text);
    document.getElementById(typingId)?.remove();
    appendMessage("assistant", response.reply, response.tools_used);
  } catch (error) {
    document.getElementById(typingId)?.remove();
    appendMessage("assistant", `⚠️ ${error.message}`);
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (text) sendMessage(text);
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => sendMessage(chip.dataset.suggestion));
});

appendMessage("assistant", `Olá, ${user?.name?.split(" ")[0] || "aluno"}! 👋 Sou o assistente da GymFlow. Pergunte sobre vagas, horários ou suas reservas.`);

// ---------- Inicialização ----------
loadCategories();
loadClasses();
