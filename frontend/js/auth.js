// auth.js - Authentication page JavaScript
document.addEventListener("DOMContentLoaded", function () {
  initializeAuthPage();
});

function initializeAuthPage() {
  try {
    setupAuthTabs();
    setupPasswordToggles();
    setupPasswordStrength();
    setupFormValidation();
    loadGoogleAuth();
    checkUrlParameters();
  } catch (e) {
    console.error("Auth initialization error:", e);
  }
}

function checkUrlParameters() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get("tab");

    if (tab === "register") {
      setTimeout(() => {
        showAuthTab("register");
      }, 100);
      return;
    }

    // Fallback: support hash like #register
    if (
      window.location.hash &&
      window.location.hash.toLowerCase().includes("register")
    ) {
      setTimeout(() => showAuthTab("register"), 100);
    }

    // Listen for hash changes too
    window.addEventListener("hashchange", () => {
      if (
        window.location.hash &&
        window.location.hash.toLowerCase().includes("register")
      ) {
        showAuthTab("register");
      } else if (
        window.location.hash &&
        window.location.hash.toLowerCase().includes("login")
      ) {
        showAuthTab("login");
      }
    });
  } catch (e) {
    console.error("checkUrlParameters error:", e);
  }
}

function setupAuthTabs() {
  const loginTab = document.getElementById("login-tab");
  const registerTab = document.getElementById("register-tab");

  document.querySelectorAll(".auth-tab").forEach((tab) => {
    tab.addEventListener("click", function () {
      // Remove active class from all tabs and forms
      document
        .querySelectorAll(".auth-tab")
        .forEach((t) => t.classList.remove("active"));
      document
        .querySelectorAll(".auth-form")
        .forEach((f) => f.classList.remove("active"));

      // Add active class to clicked tab
      this.classList.add("active");

      // Use data-target attribute to find the target form (more robust)
      const target = this.dataset.target;
      const targetForm = target
        ? document.getElementById(target + "-tab")
        : null;
      if (targetForm) {
        targetForm.classList.add("active");
        // Scroll form into view for better UX
        setTimeout(() => {
          targetForm.scrollIntoView({ behavior: "smooth", block: "center" });
        }, 50);
      }
    });
  });
}

function showAuthTab(tabName) {
  try {
    const loginTab = document.getElementById("login-tab");
    const registerTab = document.getElementById("register-tab");
    const loginTabBtn = document.querySelector(
      '.auth-tab[data-target="login"]',
    );
    const registerTabBtn = document.querySelector(
      '.auth-tab[data-target="register"]',
    );

    // Remove active from all
    document
      .querySelectorAll(".auth-tab")
      .forEach((t) => t.classList.remove("active"));
    document
      .querySelectorAll(".auth-form")
      .forEach((f) => f.classList.remove("active"));

    if (tabName === "login") {
      loginTab.classList.add("active");
      if (loginTabBtn) loginTabBtn.classList.add("active");
      if (registerTabBtn) registerTabBtn.classList.remove("active");
      // Scroll into view
      setTimeout(
        () => loginTab.scrollIntoView({ behavior: "smooth", block: "center" }),
        50,
      );
    } else if (tabName === "register") {
      registerTab.classList.add("active");
      if (registerTabBtn) registerTabBtn.classList.add("active");
      if (loginTabBtn) loginTabBtn.classList.remove("active");
      setTimeout(
        () =>
          registerTab.scrollIntoView({ behavior: "smooth", block: "center" }),
        50,
      );
    }
  } catch (e) {
    console.error("showAuthTab error:", e);
  }
}

function setupPasswordToggles() {
  const buttons = document.querySelectorAll(".toggle-password");
  if (!buttons || buttons.length === 0) return;

  buttons.forEach((button) => {
    button.addEventListener("click", function () {
      const input = this.previousElementSibling;
      const icon = this.querySelector("i");

      if (!input) return;

      if (input.type === "password") {
        input.type = "text";
        if (icon) {
          icon.classList.remove("fa-eye");
          icon.classList.add("fa-eye-slash");
        }
      } else {
        input.type = "password";
        if (icon) {
          icon.classList.remove("fa-eye-slash");
          icon.classList.add("fa-eye");
        }
      }
    });
  });
}

function togglePassword(inputId) {
  const input = document.getElementById(inputId);
  const button = input.nextElementSibling;
  const icon = button.querySelector("i");

  if (input.type === "password") {
    input.type = "text";
    icon.classList.remove("fa-eye");
    icon.classList.add("fa-eye-slash");
  } else {
    input.type = "password";
    icon.classList.remove("fa-eye-slash");
    icon.classList.add("fa-eye");
  }
}

function setupPasswordStrength() {
  const passwordInput = document.getElementById("register-password");
  const strengthMeter = document.getElementById("password-strength");
  const strengthText = document.getElementById("strength-text");

  if (!passwordInput || !strengthMeter || !strengthText) return;

  passwordInput.addEventListener("input", function () {
    const password = this.value;
    const strength = calculatePasswordStrength(password);

    // Update strength meter
    strengthMeter.style.width = strength.percentage + "%";

    // Update strength text and color
    strengthText.textContent = strength.text;
    strengthMeter.style.backgroundColor = strength.color;

    // Update text color
    strengthText.style.color = strength.color;
  });
}

function calculatePasswordStrength(password) {
  let score = 0;

  // Length check
  if (password.length >= 8) score += 25;
  if (password.length >= 12) score += 25;

  // Character variety checks
  if (/[a-z]/.test(password)) score += 10; // lowercase
  if (/[A-Z]/.test(password)) score += 10; // uppercase
  if (/[0-9]/.test(password)) score += 10; // numbers
  if (/[^A-Za-z0-9]/.test(password)) score += 10; // special characters

  // Determine strength level
  let strength = {
    percentage: Math.min(score, 100),
    text: "",
    color: "",
  };

  if (score < 30) {
    strength.text = "Mật khẩu yếu";
    strength.color = "#ff4444";
  } else if (score < 60) {
    strength.text = "Mật khẩu trung bình";
    strength.color = "#ffaa00";
  } else if (score < 80) {
    strength.text = "Mật khẩu khá mạnh";
    strength.color = "#00aa44";
  } else {
    strength.text = "Mật khẩu mạnh";
    strength.color = "#00aa44";
  }

  return strength;
}

function setupFormValidation() {
  try {
    const confirmPassword = document.getElementById(
      "register-confirm-password",
    );
    const password = document.getElementById("register-password");
    if (!confirmPassword || !password) return;

    confirmPassword.addEventListener("input", function () {
      if (this.value !== password.value) {
        this.setCustomValidity("Mật khẩu xác nhận không khớp");
      } else {
        this.setCustomValidity("");
      }
    });

    password.addEventListener("input", function () {
      if (confirmPassword.value && this.value !== confirmPassword.value) {
        confirmPassword.setCustomValidity("Mật khẩu xác nhận không khớp");
      } else {
        confirmPassword.setCustomValidity("");
      }
    });
  } catch (e) {
    console.error("setupFormValidation error:", e);
  }
}

async function handleLogin(event) {
  event.preventDefault();

  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  const rememberMe = document.getElementById("remember-me").checked;

  // Basic validation
  if (!email || !password) {
    showAuthMessage("Vui lòng nhập đầy đủ thông tin", "error");
    return;
  }

  // Show loading
  const submitBtn = event.target.querySelector(".auth-submit");
  const originalText = submitBtn.innerHTML;
  submitBtn.innerHTML =
    '<i class="fas fa-spinner fa-spin"></i> Đang đăng nhập...';
  submitBtn.disabled = true;

  try {
    // Here you would make API call to login
    // For now, simulate login
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Simulate successful login
    localStorage.setItem("token", "fake-jwt-token");
    // store user name (use part before @ if available)
    const name =
      email && email.includes("@") ? email.split("@")[0] : email || "User";
    localStorage.setItem("user", JSON.stringify({ name }));

    showAuthMessage("Đăng nhập thành công!", "success");

    // Redirect to dashboard
    setTimeout(() => {
      window.location.href = "dashboard.html";
    }, 1000);
  } catch (error) {
    console.error("Login error:", error);
    showAuthMessage("Đăng nhập thất bại. Vui lòng thử lại.", "error");
  } finally {
    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
  }
}

async function handleRegister(event) {
  event.preventDefault();

  const formData = {
    firstName: document.getElementById("register-firstname").value,
    lastName: document.getElementById("register-lastname").value,
    email: document.getElementById("register-email").value,
    password: document.getElementById("register-password").value,
    confirmPassword: document.getElementById("register-confirm-password").value,
    agreeTerms: document.getElementById("agree-terms").checked,
    subscribeNewsletter: document.getElementById("subscribe-newsletter")
      .checked,
  };

  // Validation
  if (
    !formData.firstName ||
    !formData.lastName ||
    !formData.email ||
    !formData.password
  ) {
    showAuthMessage("Vui lòng nhập đầy đủ thông tin", "error");
    return;
  }

  if (formData.password !== formData.confirmPassword) {
    showAuthMessage("Mật khẩu xác nhận không khớp", "error");
    return;
  }

  if (!formData.agreeTerms) {
    showAuthMessage("Vui lòng đồng ý với điều khoản sử dụng", "error");
    return;
  }

  // Show loading
  const submitBtn = event.target.querySelector(".auth-submit");
  const originalText = submitBtn.innerHTML;
  submitBtn.innerHTML =
    '<i class="fas fa-spinner fa-spin"></i> Đang tạo tài khoản...';
  submitBtn.disabled = true;

  try {
    // Here you would make API call to register
    // For now, simulate registration
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Simulate successful registration
    showAuthMessage(
      "Tạo tài khoản thành công! Vui lòng kiểm tra email để xác nhận.",
      "success",
    );

    // Switch to login tab
    setTimeout(() => {
      showAuthTab("login");
    }, 2000);
  } catch (error) {
    console.error("Register error:", error);
    showAuthMessage("Tạo tài khoản thất bại. Vui lòng thử lại.", "error");
  } finally {
    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
  }
}

function loadGoogleAuth() {
  // Load Google Sign-In API
  if (typeof gapi !== "undefined") {
    gapi.load("auth2", function () {
      gapi.auth2.init({
        client_id: "YOUR_GOOGLE_CLIENT_ID",
      });
    });
  }
}

function signInWithGoogle() {
  if (typeof gapi !== "undefined" && gapi.auth2) {
    const auth2 = gapi.auth2.getAuthInstance();
    auth2
      .signIn()
      .then(function (googleUser) {
        const profile = googleUser.getBasicProfile();
        console.log("Google sign in successful:", profile.getName());

        // Here you would send the Google token to your backend
        // For now, simulate successful login
        localStorage.setItem("token", "fake-google-jwt-token");
        localStorage.setItem(
          "user",
          JSON.stringify({ name: profile.getName() }),
        );
        showAuthMessage("Đăng nhập Google thành công!", "success");

        setTimeout(() => {
          window.location.href = "dashboard.html";
        }, 1000);
      })
      .catch(function (error) {
        console.error("Google sign in error:", error);
        showAuthMessage("Đăng nhập Google thất bại", "error");
      });
  } else {
    showAuthMessage("Google Sign-In chưa được tải. Vui lòng thử lại.", "error");
  }
}

function showAuthMessage(message, type = "info") {
  // Remove existing messages
  const existingMessages = document.querySelectorAll(".auth-message");
  existingMessages.forEach((msg) => msg.remove());

  // Create new message
  const messageDiv = document.createElement("div");
  messageDiv.className = `auth-message ${type}`;
  messageDiv.innerHTML = `
        <i class="fas ${type === "success" ? "fa-check-circle" : type === "error" ? "fa-exclamation-circle" : "fa-info-circle"}"></i>
        ${message}
    `;

  // Add to auth container
  const authContainer = document.querySelector(".auth-container");
  authContainer.insertBefore(messageDiv, authContainer.firstChild);

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (messageDiv.parentNode) {
      messageDiv.remove();
    }
  }, 5000);
}

// Add auth message styles
const authStyle = document.createElement("style");
authStyle.textContent = `
    .auth-message {
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 500;
        animation: slideDown 0.3s ease;
    }

    .auth-message.success {
        background: rgba(76, 175, 80, 0.1);
        border: 1px solid #4CAF50;
        color: #4CAF50;
    }

    .auth-message.error {
        background: rgba(244, 67, 54, 0.1);
        border: 1px solid #f44336;
        color: #f44336;
    }

    .auth-message.info {
        background: rgba(33, 150, 243, 0.1);
        border: 1px solid #2196F3;
        color: #2196F3;
    }

    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .password-input {
        position: relative;
    }

    .toggle-password {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.6);
        cursor: pointer;
        padding: 5px;
    }

    .password-strength {
        margin-top: 8px;
    }

    .strength-meter {
        height: 4px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 2px;
        overflow: hidden;
        margin-bottom: 4px;
    }

    .strength-fill {
        height: 100%;
        border-radius: 2px;
        transition: width 0.3s ease, background-color 0.3s ease;
    }
`;
document.head.appendChild(authStyle);
