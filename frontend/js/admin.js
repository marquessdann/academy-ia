requireAdmin();

const user = Auth.getUser();
document.getElementById("user-name").textContent = user?.name || "Admin";
document.getElementById("user-avatar").textContent = user ? initials(user.name) : "--";

document.getElementById("logout-btn").addEventListener("click", () => {
  Auth.clear();
  window.location.href = "index.html";
});

// ---------- Navegação ----------
const navLinks = document.querySelectorAll(".nav-link");
const viewIds = ["overview", "manage-classes", "manage-categories", "manage-instructors"];

navLinks.forEach((link) => {
  link.addEventListener("click", () => {
    navLinks.forEach((l) => l.classList.remove("active"));
    link.classList.add("active");
    viewIds.forEach((id) => document.getElementById(`view-${id}`).classList.toggle("hidden", id !== link.dataset.view));
  });
});

// ---------- Visão geral ----------
async function loadOverview() {
  try {
    const [occupancy, quiet] = await Promise.all([Api.occupancyReport(), Api.quietestTimes()]);

    const totalClasses = occupancy.length;
    const totalBooked = occupancy.reduce((sum, c) => sum + c.booked_count, 0);
    const avgRate = totalClasses ? occupancy.reduce((sum, c) => sum + c.occupancy_rate, 0) / totalClasses : 0;

    document.getElementById("stat-grid").innerHTML = `
      <div class="stat-card"><div class="label">Aulas cadastradas</div><div class="value">${totalClasses}</div></div>
      <div class="stat-card"><div class="label">Reservas ativas (total)</div><div class="value accent">${totalBooked}</div></div>
      <div class="stat-card"><div class="label">Ocupação média</div><div class="value">${(avgRate * 100).toFixed(0)}%</div></div>
    `;

    const occupancyBody = document.querySelector("#occupancy-table tbody");
    occupancyBody.innerHTML = occupancy.length
      ? occupancy
          .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
          .map(
            (c) => `
        <tr>
          <td>${c.title}</td>
          <td>${formatDateTime(c.start_time)}</td>
          <td>${c.booked_count}/${c.capacity}</td>
          <td>${(c.occupancy_rate * 100).toFixed(0)}%</td>
        </tr>`
          )
          .join("")
      : `<tr><td colspan="4">Nenhuma aula cadastrada ainda.</td></tr>`;

    const quietBody = document.querySelector("#quiet-table tbody");
    quietBody.innerHTML = quiet.length
      ? quiet
          .map(
            (s) => `
        <tr>
          <td>${s.day_name}</td>
          <td>${String(s.hour).padStart(2, "0")}:00</td>
          <td>${(s.average_occupancy_rate * 100).toFixed(0)}%</td>
          <td>${s.sample_size}</td>
        </tr>`
          )
          .join("")
      : `<tr><td colspan="4">Sem dados suficientes ainda.</td></tr>`;
  } catch (error) {
    showToast(error.message, "error");
  }
}

// ---------- Aulas ----------
const classCategorySelect = document.getElementById("class-category");
const classInstructorSelect = document.getElementById("class-instructor");

async function populateClassFormOptions() {
  const [categories, instructors] = await Promise.all([Api.listCategories(), Api.listInstructors()]);
  classCategorySelect.innerHTML = categories.map((c) => `<option value="${c.id}">${c.name}</option>`).join("");
  classInstructorSelect.innerHTML = instructors.map((i) => `<option value="${i.id}">${i.name}</option>`).join("");
}

async function loadClassesTable() {
  const tbody = document.querySelector("#classes-table tbody");
  try {
    const classes = await Api.listClasses();
    tbody.innerHTML = classes.length
      ? classes
          .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
          .map(
            (c) => `
        <tr>
          <td>${c.title}</td>
          <td>${c.category.name}</td>
          <td>${c.instructor.name}</td>
          <td>${formatDateTime(c.start_time)}</td>
          <td>${c.booked_count}/${c.capacity}</td>
        </tr>`
          )
          .join("")
      : `<tr><td colspan="5">Nenhuma aula cadastrada ainda.</td></tr>`;
  } catch (error) {
    tbody.innerHTML = `<tr><td colspan="5">⚠️ ${error.message}</td></tr>`;
  }
}

document.getElementById("class-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    title: document.getElementById("class-title").value.trim(),
    category_id: Number(classCategorySelect.value),
    instructor_id: Number(classInstructorSelect.value),
    start_time: document.getElementById("class-start").value,
    end_time: document.getElementById("class-end").value,
    capacity: Number(document.getElementById("class-capacity").value),
  };

  try {
    await Api.createClass(payload);
    showToast("Aula criada com sucesso!", "success");
    event.target.reset();
    document.getElementById("class-capacity").value = 20;
    loadClassesTable();
    loadOverview();
  } catch (error) {
    showToast(error.message, "error");
  }
});

// ---------- Modalidades ----------
async function loadCategoriesList() {
  const container = document.getElementById("categories-list");
  try {
    const categories = await Api.listCategories();
    container.innerHTML = categories.length
      ? categories
          .map(
            (c) => `
        <div class="list-item">
          <div class="info"><h4>${c.name}</h4><p>${c.description || "Sem descrição"}</p></div>
        </div>`
          )
          .join("")
      : `<div class="empty-state"><p>Nenhuma modalidade cadastrada.</p></div>`;
  } catch (error) {
    container.innerHTML = `<div class="empty-state">⚠️ ${error.message}</div>`;
  }
}

document.getElementById("category-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    name: document.getElementById("category-name").value.trim(),
    description: document.getElementById("category-description").value.trim() || null,
  };
  try {
    await Api.createCategory(payload);
    showToast("Modalidade criada!", "success");
    event.target.reset();
    loadCategoriesList();
    populateClassFormOptions();
  } catch (error) {
    showToast(error.message, "error");
  }
});

// ---------- Professores ----------
async function loadInstructorsList() {
  const container = document.getElementById("instructors-list");
  try {
    const instructors = await Api.listInstructors();
    container.innerHTML = instructors.length
      ? instructors
          .map(
            (i) => `
        <div class="list-item">
          <div class="info"><h4>${i.name}</h4><p>${i.specialty || "Sem especialidade"} · ${i.email}</p></div>
        </div>`
          )
          .join("")
      : `<div class="empty-state"><p>Nenhum professor cadastrado.</p></div>`;
  } catch (error) {
    container.innerHTML = `<div class="empty-state">⚠️ ${error.message}</div>`;
  }
}

document.getElementById("instructor-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    name: document.getElementById("instructor-name").value.trim(),
    email: document.getElementById("instructor-email").value.trim(),
    specialty: document.getElementById("instructor-specialty").value.trim() || null,
  };
  try {
    await Api.createInstructor(payload);
    showToast("Professor cadastrado!", "success");
    event.target.reset();
    loadInstructorsList();
    populateClassFormOptions();
  } catch (error) {
    showToast(error.message, "error");
  }
});

// ---------- Inicialização ----------
loadOverview();
populateClassFormOptions();
loadClassesTable();
loadCategoriesList();
loadInstructorsList();
