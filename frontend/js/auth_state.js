// auth_state.js - manage auth state across pages
(function () {
  function getUser() {
    try {
      const token = localStorage.getItem("token");
      const user = localStorage.getItem("user");
      return token ? (user ? JSON.parse(user) : { name: "User" }) : null;
    } catch (e) {
      console.error("getUser parse error", e);
      return null;
    }
  }

  function setLoggedInUI(user) {
    // Find nav container
    const navLinks = document.querySelector(".nav-links");
    if (!navLinks) return;

    // Remove existing login/register buttons
    navLinks
      .querySelectorAll(".btn-login, .btn-register")
      .forEach((el) => el.remove());

    // Create user menu with avatar and dropdown
    const userWrap = document.createElement("div");
    userWrap.className = "nav-user";
    const initials = (user.name || "U").trim()[0].toUpperCase();
    userWrap.innerHTML = `
      <div class="nav-user-button" tabindex="0">
        <div class="nav-user-avatar">${escapeHtml(initials)}</div>
        <div class="nav-user-info">
          <div class="nav-user-name">${escapeHtml(user.name || "User")}</div>
          <div class="nav-user-role">CodeQuest Member</div>
        </div>
        <div class="nav-user-caret">▾</div>
      </div>
      <div class="nav-user-dropdown">
        <a href="/dashboard.html" class="nav-user-item">Dashboard</a>
        <a href="/profile" class="nav-user-item">Cập nhật thông tin</a>
        <button id="nav-logout-btn" class="nav-user-item nav-user-logout">Đăng xuất</button>
      </div>
    `;

    navLinks.appendChild(userWrap);

    // Dropdown behavior
    const btn = userWrap.querySelector(".nav-user-button");
    const dropdown = userWrap.querySelector(".nav-user-dropdown");
    function closeDropdown() {
      dropdown.classList.remove("open");
    }
    function openDropdown() {
      dropdown.classList.add("open");
    }

    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (dropdown.classList.contains("open")) closeDropdown();
      else openDropdown();
    });
    btn.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        btn.click();
      }
      if (e.key === "Escape") closeDropdown();
    });

    document.addEventListener("click", (e) => {
      if (!userWrap.contains(e.target)) closeDropdown();
    });

    const logoutBtn = document.getElementById("nav-logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        // reload to update UI
        window.location.reload();
      });
    }
  }

  function setLoggedOutUI() {
    const navLinks = document.querySelector(".nav-links");
    if (!navLinks) return;
    // Remove any existing user UI
    navLinks.querySelectorAll(".nav-user").forEach((el) => el.remove());

    // If no login button exists, add one
    if (!navLinks.querySelector(".btn-login")) {
      const loginBtn = document.createElement("button");
      loginBtn.className = "btn-login";
      loginBtn.textContent = "Đăng nhập";
      loginBtn.addEventListener(
        "click",
        () => (window.location.href = "/auth.html"),
      );
      navLinks.appendChild(loginBtn);
    }
  }

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, function (m) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[m];
    });
  }

  function init() {
    const user = getUser();
    if (user) setLoggedInUI(user);
    else setLoggedOutUI();

    // Also support immediate DOM changes on pages that have logout buttons already
    const pageLogout = document.getElementById("logoutBtn");
    if (pageLogout) {
      pageLogout.addEventListener("click", () => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.reload();
      });
    }
  }

  // Run on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
