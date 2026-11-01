// City Library demo page. Talks only to the JSON API; every rule is enforced by the server.
const state = {
  token: sessionStorage.getItem("token"),
  role: sessionStorage.getItem("role"),
  username: sessionStorage.getItem("username"),
  books: [],
  authMode: "login",
};

const $ = (sel) => document.querySelector(sel);

// Build elements with textContent only, so book titles typed by users can never inject HTML.
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "onclick") node.addEventListener("click", value);
    else if (key === "class") node.className = value;
    else node.setAttribute(key, value);
  }
  for (const child of children) node.append(child);
  return node;
}

async function api(method, url, body) {
  const headers = { "Content-Type": "application/json" };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const res = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined });
  const data = await res.json().catch(() => ({}));
  logCall(method, url, res.status, data);
  if (res.status === 401 && state.token && !url.startsWith("/auth/")) {
    // Token no longer valid (e.g. server restarted with a new database): back to guest.
    Object.assign(state, { token: null, role: null, username: null });
    sessionStorage.clear();
    renderHeader();
  }
  return { ok: res.ok, status: res.status, data };
}

function logCall(method, url, status, data) {
  const note = data && data.error ? `  ${data.error}` : "";
  const item = el("li", { class: `s${String(status)[0]}` }, `${method} ${url}  →  ${status}${note}`);
  $("#log").prepend(item);
}

let toastTimer;
function toast(message, ok = true) {
  const t = $("#toast");
  t.textContent = message;
  t.className = `toast ${ok ? "ok" : "err"}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add("hidden"), 3500);
}

function showError(res) {
  toast(`${res.status} · ${res.data.error || "request failed"}`, false);
}

const today = () => new Date().toISOString().slice(0, 10);
const daysBetween = (a, b) => Math.round((new Date(b) - new Date(a)) / 86400000);
const bookTitle = (id) => (state.books.find((b) => b.id === id) || { title: `Book #${id}` }).title;

// ---------------------------------------------------------------- header and auth
function renderHeader() {
  const who = $("#who");
  who.replaceChildren();
  if (state.token) {
    who.append(el("span", {}, "Logged in as ", el("b", {}, state.username), ` (${state.role})`),
               el("button", { onclick: logout }, "Log out"));
  } else {
    who.append(el("span", {}, "Guest"));
  }
  $("#auth").classList.toggle("hidden", !!state.token);
  $("#my-loans").classList.toggle("hidden", state.role !== "member");
  $("#admin").classList.toggle("hidden", state.role !== "admin");
}

document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === tab));
  state.authMode = tab.dataset.tab;
  $("#auth-submit").textContent = state.authMode === "login" ? "Log in" : "Create account";
}));

$("#auth-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const creds = { username: form.get("username"), password: form.get("password") };
  if (state.authMode === "register") {
    const reg = await api("POST", "/auth/register", creds);
    if (!reg.ok) return showError(reg);
    toast(`Account "${reg.data.username}" created`);
  }
  const res = await api("POST", "/auth/login", creds);
  if (!res.ok) return showError(res);
  Object.assign(state, { token: res.data.token, role: res.data.role, username: creds.username });
  for (const key of ["token", "role", "username"]) sessionStorage.setItem(key, state[key]);
  e.target.reset();
  toast(`Welcome, ${creds.username}`);
  refresh();
});

async function logout() {
  await api("POST", "/auth/logout");
  Object.assign(state, { token: null, role: null, username: null });
  sessionStorage.clear();
  toast("Logged out");
  refresh();
}

// ---------------------------------------------------------------- catalogue
async function loadBooks() {
  const q = $("#search").value.trim();
  const res = await api("GET", `/books${q ? `?q=${encodeURIComponent(q)}` : ""}`);
  state.books = res.ok ? res.data : [];
  const box = $("#books");
  box.replaceChildren();
  if (!state.books.length) box.append(el("div", { class: "empty" }, "No books found."));
  for (const b of state.books) {
    const available = b.available_copies > 0;
    const actions = el("div", { class: "actions" });
    if (state.token) {
      const borrow = el("button", { class: "primary", onclick: () => borrowBook(b.id) }, "Borrow");
      actions.append(borrow);
    }
    if (state.role === "admin") {
      actions.append(el("button", { onclick: () => editCopies(b) }, "Copies…"),
                     el("button", { class: "danger", onclick: () => deleteBook(b) }, "Delete"));
    }
    box.append(el("div", { class: "book" },
      el("div", { class: "title" }, b.title),
      el("div", { class: "meta" }, `${b.author} · ISBN ${b.isbn}`),
      el("div", {}, el("span", { class: `badge ${available ? "ok" : "none"}` },
        available ? `${b.available_copies} of ${b.total_copies} available` : `0 of ${b.total_copies} available`)),
      actions));
  }
}

let searchTimer;
$("#search").addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadBooks, 250);
});

async function borrowBook(id) {
  const res = await api("POST", "/loans", { book_id: id });
  if (!res.ok) return showError(res);
  toast(`Borrowed "${bookTitle(id)}" · due ${res.data.due_on}`);
  refresh();
}

// ---------------------------------------------------------------- loans
async function loadMyLoans() {
  if (state.role !== "member") return;
  const res = await api("GET", "/loans/me");
  const body = $("#my-loans-body");
  body.replaceChildren();
  if (!res.ok) return;
  if (!res.data.length) body.append(el("tr", {}, el("td", { colspan: 5, class: "empty" }, "No loans yet.")));
  for (const loan of res.data.slice().reverse()) {
    let status;
    if (loan.returned_on) {
      status = el("span", { class: "badge done" }, `Returned ${loan.returned_on}${loan.fine ? ` · fine Rs ${loan.fine}` : ""}`);
    } else {
      const late = daysBetween(loan.due_on, today());
      status = late > 0
        ? el("span", { class: "badge late" }, `Overdue ${late} day${late > 1 ? "s" : ""} · Rs ${late * 5}`)
        : el("span", { class: "badge ok" }, "On loan");
    }
    const action = loan.returned_on ? "" : el("button", { onclick: () => returnBook(loan) }, "Return");
    body.append(el("tr", {}, el("td", {}, bookTitle(loan.book_id)), el("td", {}, loan.borrowed_on),
      el("td", {}, loan.due_on), el("td", {}, status), el("td", {}, action)));
  }
}

async function returnBook(loan) {
  const res = await api("POST", `/loans/${loan.id}/return`);
  if (!res.ok) return showError(res);
  toast(res.data.fine ? `Returned late · fine Rs ${res.data.fine}` : "Returned on time · no fine", !res.data.fine);
  refresh();
}

// ---------------------------------------------------------------- admin
$("#book-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  const res = await api("POST", "/books", {
    isbn: f.get("isbn").trim(), title: f.get("title"), author: f.get("author"),
    total_copies: Number(f.get("total_copies")),
  });
  if (!res.ok) return showError(res);
  toast(`Added "${res.data.title}"`);
  e.target.reset();
  refresh();
});

async function editCopies(book) {
  const value = prompt(`Total copies of "${book.title}" (currently ${book.total_copies}):`, book.total_copies);
  if (value === null) return;
  const res = await api("PUT", `/books/${book.id}`, { total_copies: Number(value) });
  if (!res.ok) return showError(res);
  toast(`Copies updated to ${res.data.total_copies}`);
  refresh();
}

async function deleteBook(book) {
  if (!confirm(`Delete "${book.title}"?`)) return;
  const res = await api("DELETE", `/books/${book.id}`);
  if (!res.ok) return showError(res);
  toast("Book deleted");
  refresh();
}

async function loadAllLoans() {
  if (state.role !== "admin") return;
  const res = await api("GET", `/loans${$("#overdue-only").checked ? "?overdue=1" : ""}`);
  const body = $("#all-loans-body");
  body.replaceChildren();
  if (!res.ok) return;
  if (!res.data.length) body.append(el("tr", {}, el("td", { colspan: 6, class: "empty" }, "No loans.")));
  for (const loan of res.data) {
    body.append(el("tr", {}, el("td", {}, `#${loan.id}`), el("td", {}, `User #${loan.user_id}`),
      el("td", {}, bookTitle(loan.book_id)), el("td", {}, loan.due_on),
      el("td", {}, loan.returned_on || "-"), el("td", {}, loan.fine ? `Rs ${loan.fine}` : "-")));
  }
}
$("#overdue-only").addEventListener("change", loadAllLoans);
$("#clear-log").addEventListener("click", () => $("#log").replaceChildren());

async function refresh() {
  renderHeader();
  await loadBooks();
  await Promise.all([loadMyLoans(), loadAllLoans()]);
}

refresh();
