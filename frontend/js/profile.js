document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("profile-form");
  const nameInput = document.getElementById("profile-name");
  const emailInput = document.getElementById("profile-email");
  const avatarInput = document.getElementById("profile-avatar");
  const bioInput = document.getElementById("profile-bio");
  const msg = document.getElementById("profile-message");
  const avatarCircle = document.getElementById("avatarCircle");

<<<<<<< HEAD
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

=======
  function getInitials(name) {
    const s = String(name || "U").trim();
    return (s[0] || "U").toUpperCase();
  }

  function setAvatarPreview(name, avatarUrl) {
    if (!avatarCircle) return;
    const initials = getInitials(name);
    if (!avatarUrl) {
      avatarCircle.innerHTML = initials;
      return;
    }
    // Render img; fallback to initials on error
    avatarCircle.innerHTML = `
      <img src="${escapeHtml(avatarUrl)}" alt="avatar" referrerpolicy="no-referrer" />
    `;
    const img = avatarCircle.querySelector("img");
    if (img) {
      img.onerror = () => {
        avatarCircle.textContent = initials;
      };
    }
  }

  function escapeHtml(str) {
    return String(str).replace(/[&<>"]/g, (m) => {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
      }[m];
    });
  }

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

  // Load from backend first (authoritative for name/email), then merge local-only fields
>>>>>>> da00585 (đổi sqlite sang mysql(mysqlxampp)mysqlxampp)
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
<<<<<<< HEAD
    if (merged.avatarUrl) avatarInput.value = merged.avatarUrl;
    if (merged.bio) bioInput.value = merged.bio;
  })();

  form.addEventListener("submit", function (e) {
=======
    if (merged.avatarUrl || merged.avatar_url)
      avatarInput.value = merged.avatarUrl || merged.avatar_url;
    if (merged.bio) bioInput.value = merged.bio;

    setAvatarPreview(merged.name, merged.avatarUrl || merged.avatar_url);
  })();

  if (avatarInput) {
    avatarInput.addEventListener("input", () => {
      setAvatarPreview(nameInput.value, avatarInput.value.trim());
    });
  }

  if (nameInput) {
    nameInput.addEventListener("input", () => {
      setAvatarPreview(nameInput.value, avatarInput.value.trim());
    });
  }

  async function patchProfileToBackendIfPossible(user) {
    const token = localStorage.getItem("token");
    if (!token || String(token).startsWith("fake")) return null;

    try {
      const res = await fetch("/api/auth/profile", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: user.name,
          avatar_url: user.avatarUrl || "",
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "Cập nhật backend thất bại");
      }
      return await res.json();
    } catch (e) {
      console.warn("Profile PATCH failed", e);
      return null;
    }
  }

  form.addEventListener("submit", async function (e) {
>>>>>>> da00585 (đổi sqlite sang mysql(mysqlxampp)mysqlxampp)
    e.preventDefault();
    const user = {
      name: nameInput.value.trim() || "User",
      email: emailInput.value.trim(),
      avatarUrl: avatarInput.value.trim(),
      bio: bioInput.value.trim(),
    };

    // Persist locally for immediate UI updates
    localStorage.setItem("user", JSON.stringify(user));

    // Best-effort persist to backend (name + avatar_url)
    const remote = await patchProfileToBackendIfPossible(user);
    if (remote) {
      const merged = {
        ...user,
        name: remote.name || user.name,
        email: remote.email || user.email,
        avatarUrl: remote.avatar_url || user.avatarUrl,
      };
      localStorage.setItem("user", JSON.stringify(merged));
    }

    msg.textContent = "Lưu thông tin thành công!";
    setTimeout(() => {
      msg.textContent = "";
      window.location.href = "/";
    }, 800);
  });

  document
    .getElementById("profile-cancel")
    .addEventListener("click", function () {
      window.location.href = "/";
    });
});
