document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("profile-form");
  const nameInput = document.getElementById("profile-name");
  const emailInput = document.getElementById("profile-email");
  const avatarInput = document.getElementById("profile-avatar");
  const bioInput = document.getElementById("profile-bio");
  const msg = document.getElementById("profile-message");

  // Load from localStorage if available
  try {
    const user = localStorage.getItem("user");
    if (user) {
      const u = JSON.parse(user);
      if (u.name) nameInput.value = u.name;
      if (u.email) emailInput.value = u.email;
      if (u.avatarUrl) avatarInput.value = u.avatarUrl;
      if (u.bio) bioInput.value = u.bio;
    }
  } catch (e) {
    console.error(e);
  }

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
