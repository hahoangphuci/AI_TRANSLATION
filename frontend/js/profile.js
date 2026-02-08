document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("profile-form");
  const nameInput = document.getElementById("profile-name");
  const emailInput = document.getElementById("profile-email");
  const avatarInput = document.getElementById("profile-avatar");
  const bioInput = document.getElementById("profile-bio");
  const msg = document.getElementById("profile-message");
  const avatarCircle = document.getElementById("avatarCircle");

  if (!form) return;

  function escapeHtml(str) {
    return String(str).replace(/[&<>\"]/g, (m) => {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
      }[m];
    });
  }

  function getInitials(name) {
    const s = String(name || "U").trim();
    return (s[0] || "U").toUpperCase();
  }

  function setAvatarPreview(name, avatarUrl) {
    if (!avatarCircle) return;
    const initials = getInitials(name);
    if (!avatarUrl) {
      avatarCircle.textContent = initials;
      return;
    }
    avatarCircle.innerHTML = `<img src="${escapeHtml(avatarUrl)}" alt="avatar" referrerpolicy="no-referrer" />`;
    const img = avatarCircle.querySelector("img");
    if (img) {
      img.onerror = () => {
        avatarCircle.textContent = initials;
      };
    }
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

  (async () => {
    let local = null;
    try {
      const cached = localStorage.getItem("user");
      local = cached ? JSON.parse(cached) : null;
    } catch (e) {
      local = null;
    }

    const remote = await loadProfileFromBackendIfPossible();
    const merged = { ...(local || {}), ...(remote || {}) };
    if (remote) localStorage.setItem("user", JSON.stringify(merged));

    if (nameInput && merged.name) nameInput.value = merged.name;
    if (emailInput && merged.email) emailInput.value = merged.email;
    if (avatarInput && (merged.avatarUrl || merged.avatar_url))
      avatarInput.value = merged.avatarUrl || merged.avatar_url;
    if (bioInput && merged.bio) bioInput.value = merged.bio;

    setAvatarPreview(merged.name, merged.avatarUrl || merged.avatar_url);
  })();

  if (avatarInput) {
    avatarInput.addEventListener("input", () => {
      setAvatarPreview(
        nameInput ? nameInput.value : "",
        avatarInput.value.trim(),
      );
    });
  }

  if (nameInput) {
    nameInput.addEventListener("input", () => {
      setAvatarPreview(
        nameInput.value,
        avatarInput ? avatarInput.value.trim() : "",
      );
    });
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const user = {
      name: (nameInput ? nameInput.value.trim() : "") || "User",
      email: emailInput ? emailInput.value.trim() : "",
      avatarUrl: avatarInput ? avatarInput.value.trim() : "",
      bio: bioInput ? bioInput.value.trim() : "",
    };

    localStorage.setItem("user", JSON.stringify(user));

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

    if (msg) msg.textContent = "Lưu thông tin thành công!";
    setTimeout(() => {
      if (msg) msg.textContent = "";
      window.location.href = "/";
    }, 800);
  });

  const cancel = document.getElementById("profile-cancel");
  if (cancel) {
    cancel.addEventListener("click", function () {
      window.location.href = "/";
    });
  }
});
