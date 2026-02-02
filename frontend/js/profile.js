document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("profile-form");
  const nameInput = document.getElementById("profile-name");
  const emailInput = document.getElementById("profile-email");
  const avatarInput = document.getElementById("profile-avatar");
  const bioInput = document.getElementById("profile-bio");
  const msg = document.getElementById("profile-message");

  async function loadProfileFromBackendIfPossible() {
    const token = localStorage.getItem("token");
    if (!token || String(token).startsWith("fake")) return null;

    try {
      const res = await fetch("/api/auth/profile", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return null;
      return await res.json();
    } catch (e) {
      console.warn("Failed to fetch /api/auth/profile", e);
      return null;
    }
  }

  (async () => {
    let local = null;
    try {
      const user = localStorage.getItem("user");
      local = user ? JSON.parse(user) : null;
    } catch (e) {
      local = null;
    }

    const remote = await loadProfileFromBackendIfPossible();
    const merged = { ...(local || {}), ...(remote || {}) };
    if (remote) localStorage.setItem("user", JSON.stringify(merged));

    if (merged.name) nameInput.value = merged.name;
    if (merged.email) emailInput.value = merged.email;
    if (merged.avatarUrl) avatarInput.value = merged.avatarUrl;
    if (merged.bio) bioInput.value = merged.bio;
  })();

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const user = {
      name: nameInput.value.trim() || "User",
      email: emailInput.value.trim(),
      avatarUrl: avatarInput.value.trim(),
      bio: bioInput.value.trim(),
    };
    localStorage.setItem("user", JSON.stringify(user));
    msg.textContent = "Lưu thông tin thành công!";
    setTimeout(() => {
      msg.textContent = "";
      window.location.reload();
    }, 1000);
  });

  document
    .getElementById("profile-cancel")
    .addEventListener("click", function () {
      window.location.href = "/";
    });
});
