// auth.js - Authentication module
class AuthManager {
  constructor() {
    this.token = localStorage.getItem("token");
  }

  isAuthenticated() {
    // Re-check localStorage in case token changes between page loads
    this.token = localStorage.getItem("token");
    return !!this.token;
  }

  redirectToLogin() {
    window.location.href = "auth.html";
  }

  logout() {
    localStorage.removeItem("token");
    this.updateAuthUI();
    // Redirect to auth page after logout
    setTimeout(() => {
      window.location.href = "auth.html";
    }, 500);
  }

  getAuthHeaders() {
    // Return authorization header if token is present and is a real JWT (not fake dev token)
    this.token = localStorage.getItem("token");
    if (this.token && !String(this.token).startsWith("fake")) {
      return { Authorization: `Bearer ${this.token}` };
    }
    return {};
  }

  async loadUserInfo() {
    // If no token, skip
    this.token = localStorage.getItem("token");
    if (!this.token) return null;

    // Development helper: if token starts with 'fake', load profile from localStorage to avoid hitting backend JWT checks
    if (this.token.startsWith && this.token.startsWith("fake")) {
      try {
        const cached = localStorage.getItem("user");
        const parsed = cached ? JSON.parse(cached) : null;
        const nameEl = document.getElementById("userName");
        if (nameEl) nameEl.textContent = (parsed && parsed.name) || "User";
        return parsed || { name: "User" };
      } catch (e) {
        console.warn("Failed to parse cached user", e);
        return { name: "User" };
      }
    }

    try {
      const response = await fetch("/api/auth/profile", {
        headers: {
          Authorization: `Bearer ${this.token}`,
        },
      });

      if (!response.ok) {
        console.warn("Profile fetch failed with status", response.status);
        // If token invalid or unprocessable, force logout and return null
        if ([401, 422].includes(response.status)) {
          this.logout();
          return null;
        }
        return null;
      }

      const data = await response.json();
      const nameEl = document.getElementById("userName");
      if (nameEl) nameEl.textContent = data.name || "User";
      return data;
    } catch (error) {
      console.error("Error loading user info:", error);
      const nameEl = document.getElementById("userName");
      if (nameEl) nameEl.textContent = "User";
      return null;
    }
  }

  updateAuthUI() {
    const loginBtn = document.getElementById("loginBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const userInfo = document.querySelector(".user-info");

    if (this.isAuthenticated()) {
      // User is logged in
      if (loginBtn) loginBtn.style.display = "none";
      if (logoutBtn) logoutBtn.style.display = "inline-block";
      if (userInfo) userInfo.style.display = "flex";
    } else {
      // User is not logged in
      if (loginBtn) loginBtn.style.display = "inline-block";
      if (logoutBtn) logoutBtn.style.display = "none";
      if (userInfo) userInfo.style.display = "none";
    }
  }
}

// UI Manager
class UIManager {
  static showTab(tabName) {
    try {
      console.debug("[UI] showTab called for", tabName);
      // Hide all tabs
      document.querySelectorAll(".tab-content").forEach((tab) => {
        tab.classList.remove("active");
      });

      // Remove active class from all buttons
      document.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.classList.remove("active");
      });

      // Show selected tab (guard if missing)
      const tabEl = document.getElementById(tabName + "-tab");
      if (tabEl) {
        tabEl.classList.add("active");
      } else {
        console.warn("[UI] Tab element not found:", tabName + "-tab");
      }

      // Add active class to the corresponding button (do not rely on global event)
      let button =
        document.querySelector(`.tab-btn[onclick="showTab('${tabName}')"]`) ||
        document.querySelector(`.tab-btn[onclick='showTab("${tabName}")']`);
      // Fallback: match by normalized text
      if (!button) {
        const normalized = (tabName || "").toLowerCase().replace(/\s+/g, "");
        button = Array.from(document.querySelectorAll(".tab-btn")).find((b) => {
          const text = (b.textContent || "").toLowerCase().replace(/\s+/g, "");
          return text === normalized;
        });
      }
      if (button) button.classList.add("active");
      else console.warn("[UI] Tab button not found for", tabName);
    } catch (err) {
      console.error("[UI] showTab error:", err);
    }
  }

  static showLoading(button, text = "Đang xử lý...") {
    const originalText = button.innerHTML;
    button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
    button.disabled = true;
    return originalText;
  }

  static hideLoading(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
  }

  static showAlert(message, type = "error") {
    // Simple alert for now, can be enhanced with toast notifications
    alert(message);
  }

  static showNotification(message, type = "info") {
    const notificationArea = document.getElementById("notificationArea");
    const notificationText = document.getElementById("notificationText");

    if (notificationArea && notificationText) {
      // Update notification content
      notificationText.textContent = message;

      // Update icon based on type
      const iconElement = notificationArea.querySelector("i");
      switch (type) {
        case "success":
          iconElement.className = "fas fa-check-circle";
          notificationArea.style.borderColor = "rgba(40, 167, 69, 0.3)";
          notificationArea.style.background = "rgba(40, 167, 69, 0.1)";
          break;
        case "error":
          iconElement.className = "fas fa-exclamation-triangle";
          notificationArea.style.borderColor = "rgba(220, 53, 69, 0.3)";
          notificationArea.style.background = "rgba(220, 53, 69, 0.1)";
          break;
        default:
          iconElement.className = "fas fa-info-circle";
          notificationArea.style.borderColor = "rgba(255, 215, 0, 0.3)";
          notificationArea.style.background = "rgba(255, 215, 0, 0.1)";
      }

      // Show notification
      notificationArea.style.display = "block";

      // Auto hide after 5 seconds
      setTimeout(() => {
        UIManager.hideNotification();
      }, 5000);
    } else {
      // Fallback to old notification system
      this.showToastNotification(message, type);
    }
  }

  static hideNotification() {
    const notificationArea = document.getElementById("notificationArea");
    if (notificationArea) {
      notificationArea.style.display = "none";
    }
  }

  static showToastNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.innerHTML = `
            <i class="fas ${type === "success" ? "fa-check-circle" : type === "error" ? "fa-exclamation-circle" : "fa-info-circle"}"></i>
            ${message}
        `;

    // Add to page
    document.body.appendChild(notification);

    // Show animation
    setTimeout(() => notification.classList.add("show"), 100);

    // Remove after 3 seconds
    setTimeout(() => {
      notification.classList.remove("show");
      setTimeout(() => document.body.removeChild(notification), 300);
    }, 3000);
  }

  static showError(message) {
    const errorDiv = document.getElementById("translationError");
    const errorText = document.getElementById("errorText");

    if (errorDiv && errorText) {
      errorText.textContent = message;
      errorDiv.style.display = "flex";
    } else {
      this.showNotification(message, "error");
    }
  }

  static hideError() {
    const errorDiv = document.getElementById("translationError");
    if (errorDiv) {
      errorDiv.style.display = "none";
    }
  }

  static showSuccess(message) {
    const successDiv = document.getElementById("uploadSuccess");
    const successText = document.getElementById("successText");

    if (successDiv && successText) {
      successText.textContent = message;
      successDiv.style.display = "flex";
    } else {
      this.showNotification(message, "success");
    }
  }

  static hideSuccess() {
    const successDiv = document.getElementById("uploadSuccess");
    if (successDiv) {
      successDiv.style.display = "none";
    }
  }
}

// Translation Manager
class TranslationManager {
  constructor(authManager) {
    this.auth = authManager;
    this.setupEventListeners();
  }

  setupEventListeners() {
    const inputText = document.getElementById("inputText");
    const charCount = document.getElementById("charCount");

    inputText.addEventListener("input", () => {
      const count = inputText.value.length;
      charCount.textContent = count;

      if (count > 5000) {
        charCount.style.color = "#00A8FF";
      } else {
        charCount.style.color = "rgba(255, 255, 255, 0.7)";
      }
    });
  }

  async translateText() {
    const text = document.getElementById("inputText").value.trim();
    const sourceLang = document.getElementById("sourceLang").value;
    const targetLang = document.getElementById("targetLang").value;

    // Ensure user is authenticated
    if (!this.auth.isAuthenticated()) {
      UIManager.showError("Vui lòng đăng nhập để sử dụng chức năng dịch!");
      // Optionally redirect to login after short delay
      setTimeout(() => this.auth.redirectToLogin(), 800);
      return;
    }

    if (!text) {
      UIManager.showError("Vui lòng nhập văn bản cần dịch!");
      return;
    }

    // Hide previous error
    UIManager.hideError();

    const translateBtn = document.getElementById("translateBtn");
    const translateBtnText = document.getElementById("translateBtnText");
    const translateLoading = document.getElementById("translateLoading");

    // Show loading state
    translateBtnText.textContent = "Đang dịch...";
    translateLoading.style.display = "inline-block";
    translateBtn.disabled = true;

    try {
      const response = await fetch("/api/translation/text", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...this.auth.getAuthHeaders(),
        },
        body: JSON.stringify({
          text: text,
          source_lang: sourceLang,
          target_lang: targetLang,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error ||
            errorData.message ||
            "Dịch thất bại. Kiểm tra API key (OPENAI/OPENROUTER) trong .env.",
        );
      }

      const data = await response.json();
      this.showTranslationResult(data.translated_text);

      // Reload stats and history
      dashboard.stats.loadStats();
      dashboard.history.loadHistory();
    } catch (error) {
      console.error("Translation error:", error);
      UIManager.showError(
        error.message || "Có lỗi xảy ra khi dịch. Vui lòng thử lại.",
      );
    } finally {
      // Hide loading state
      translateBtnText.textContent = "Dịch";
      translateLoading.style.display = "none";
      translateBtn.disabled = false;
    }
  }

  showTranslationResult(translatedText) {
    const resultDiv = document.getElementById("translationResult");
    const outputDiv = document.getElementById("outputText");

    outputDiv.textContent = translatedText;
    resultDiv.style.display = "block";
  }

  copyResult() {
    const outputText = document.getElementById("outputText").textContent;
    navigator.clipboard.writeText(outputText).then(() => {
      UIManager.showNotification("Đã sao chép vào clipboard!", "success");
    });
  }

  async saveTranslation() {
    const originalText = document.getElementById("inputText").value;
    const translatedText = document.getElementById("outputText").textContent;

    try {
      const response = await fetch("/api/translation/save", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...this.auth.getAuthHeaders(),
        },
        body: JSON.stringify({
          original_text: originalText,
          translated_text: translatedText,
          source_lang: document.getElementById("sourceLang").value,
          target_lang: document.getElementById("targetLang").value,
        }),
      });

      if (response.ok) {
        UIManager.showNotification("Đã lưu bản dịch!", "success");
      } else {
        throw new Error("Save failed");
      }
    } catch (error) {
      console.error("Save error:", error);
      UIManager.showAlert("Có lỗi khi lưu bản dịch.");
    }
  }
}

// History Manager
class HistoryManager {
  constructor(authManager) {
    this.auth = authManager;
    this.currentPage = 1;
    this.currentFilter = "all";
  }

  async loadHistory(page = 1, filter = "all") {
    this.currentPage = page;
    this.currentFilter = filter;

    try {
      // Dev: if token is fake, use local mock history
      const token = localStorage.getItem("token");
      if (token && token.startsWith && token.startsWith("fake")) {
        const mock = [
          {
            id: 1,
            original_text: "Hello",
            translated_text: "[DEV] Xin chào",
            source_lang: "en",
            target_lang: "vi",
            created_at: new Date().toISOString(),
            has_file: false,
          },
        ];
        this.renderHistory(mock);
        this.updatePagination(1, 1);
        return;
      }

      const params = new URLSearchParams({
        page: page,
        per_page: 10,
        type: filter,
      });

      const response = await fetch(`/api/translation/history?${params}`, {
        headers: this.auth.getAuthHeaders(),
      });

      if (!response.ok) throw new Error("Failed to load history");

      const data = await response.json();
      this.renderHistory(data.translations);
      this.updatePagination(data.pages, page);
    } catch (error) {
      console.error("Error loading history:", error);
    }
  }

  renderHistory(translations) {
    const historyList = document.getElementById("historyList");

    if (translations.length === 0) {
      historyList.innerHTML =
        '<p class="no-history">Chưa có lịch sử dịch thuật.</p>';
      return;
    }

    historyList.innerHTML = translations
      .map(
        (item) => `
            <div class="history-item glassmorphism">
                <div class="history-header">
                    <span class="history-date">${new Date(item.created_at).toLocaleString("vi-VN")}</span>
                    <span class="history-lang">${item.source_lang} → ${item.target_lang}</span>
                </div>
                <div class="history-content">
                    <div class="original-text">
                        <strong>Nguyên bản:</strong> ${item.original_text.length > 100 ? item.original_text.substring(0, 100) + "..." : item.original_text}
                    </div>
                    <div class="translated-text">
                        <strong>Dịch:</strong> ${item.translated_text.length > 100 ? item.translated_text.substring(0, 100) + "..." : item.translated_text}
                    </div>
                </div>
                <div class="history-actions">
                    <button onclick="copyHistoryItem('${item.translated_text.replace(/'/g, "\\'")}')" class="btn-small">
                        <i class="fas fa-copy"></i> Sao chép
                    </button>
                    <button onclick="deleteHistoryItem(${item.id})" class="btn-small delete">
                        <i class="fas fa-trash"></i> Xóa
                    </button>
                </div>
            </div>
        `,
      )
      .join("");
  }

  updatePagination(totalPages, currentPage) {
    const pageInfo = document.getElementById("pageInfo");
    const prevBtn = document.getElementById("prevPage");
    const nextBtn = document.getElementById("nextPage");

    pageInfo.textContent = `Trang ${currentPage} / ${totalPages}`;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
  }

  changePage(direction) {
    const newPage = this.currentPage + direction;
    if (newPage > 0) {
      this.loadHistory(newPage, this.currentFilter);
    }
  }

  filterHistory() {
    const filter = document.getElementById("historyFilter").value;
    this.loadHistory(1, filter);
  }
}

// File Upload Manager
class FileUploadManager {
  constructor(authManager) {
    this.auth = authManager;
    this.selectedFile = null;
    this.setupFileUpload();
  }

  setupFileUpload() {
    const fileInput = document.getElementById("fileInput");
    const uploadArea = document.querySelector(".upload-area");

    // Click to select file
    uploadArea.addEventListener("click", (e) => {
      // Only trigger file input if clicking on the area itself, not on buttons
      if (
        e.target === uploadArea ||
        e.target.closest(".upload-icon") ||
        e.target.tagName === "H3" ||
        e.target.tagName === "P"
      ) {
        fileInput.click();
      }
    });

    // Drag and drop (optional enhancement)
    uploadArea.addEventListener("dragover", (e) => {
      e.preventDefault();
      uploadArea.classList.add("drag-over");
    });

    uploadArea.addEventListener("dragleave", () => {
      uploadArea.classList.remove("drag-over");
    });

    uploadArea.addEventListener("drop", (e) => {
      e.preventDefault();
      uploadArea.classList.remove("drag-over");
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        this.handleFileSelect(files[0]);
      }
    });

    // File input change
    fileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        this.handleFileSelect(e.target.files[0]);
      }
    });
  }

  handleFileSelect(file) {
    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "text/plain",
    ];
    const maxSize = 50 * 1024 * 1024; // 50MB

    if (!allowedTypes.includes(file.type)) {
      UIManager.showAlert(
        "Định dạng file không được hỗ trợ. Chỉ chấp nhận PDF, Word, Excel, Text.",
      );
      return;
    }

    if (file.size > maxSize) {
      UIManager.showAlert("File quá lớn. Giới hạn 50MB.");
      return;
    }

    this.showFileInfo(file);
  }

  showFileInfo(file) {
    const fileInfo = document.getElementById("fileInfo");
    const fileName = document.getElementById("fileName");
    const fileSize = document.getElementById("fileSize");

    fileName.textContent = file.name;
    fileSize.textContent = `(${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    fileInfo.style.display = "block";
    this.selectedFile = file;
  }

  async uploadDocument() {
    if (!this.selectedFile) {
      UIManager.showError("Vui lòng chọn file trước!");
      return;
    }

    const targetLang = document.getElementById("uploadTargetLang").value;
    const uploadBtn = document.getElementById("uploadBtn");
    const uploadBtnText = document.getElementById("uploadBtnText");
    const uploadBtnLoading = document.getElementById("uploadBtnLoading");

    // Hide previous messages
    UIManager.hideError();
    UIManager.hideSuccess();

    // Show loading state
    uploadBtnText.textContent = "Đang upload...";
    uploadBtnLoading.style.display = "inline-block";
    uploadBtn.disabled = true;

    const formData = new FormData();
    formData.append("file", this.selectedFile);
    formData.append("target_lang", targetLang);

    try {
      const response = await fetch("/api/translation/document", {
        method: "POST",
        headers: this.auth.getAuthHeaders(),
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error ||
            errorData.message ||
            "Upload thất bại. Kiểm tra API key (OPENAI/OPENROUTER) trong .env.",
        );
      }

      const data = await response.json();

      // If job-based, start polling status
      if (data.job_id) {
        UIManager.showNotification(
          "Tệp đã được chấp nhận, bắt đầu xử lý. Bắt đầu theo dõi tiến trình...",
          "info",
        );
        document.getElementById("uploadProgress").style.display = "block";
        const progressFill = document.getElementById("progressFill");
        const progressText = document.getElementById("progressText");
        const progressPercent = document.getElementById("progressPercent");

        const pollUrl = data.status_url;
        const interval = setInterval(async () => {
          try {
            const statusResp = await fetch(pollUrl, {
              headers: this.auth.getAuthHeaders(),
            });
            if (!statusResp.ok) {
              throw new Error("Failed to get status");
            }
            const statusData = await statusResp.json();
            const p = statusData.progress || 0;
            progressFill.style.width = `${p}%`;
            progressPercent.textContent = `${p}%`;
            progressText.textContent = statusData.message || "Đang xử lý...";

            if (statusData.status === "completed") {
              clearInterval(interval);

              // If fallback occurred, inform user
              if (statusData.fallback) {
                UIManager.showError(
                  `File was returned as a fallback (${statusData.fallback_reason}). The file may be plain text.`,
                );
              }

              // Auto download
              if (statusData.download_url) {
                setTimeout(() => {
                  const link = document.createElement("a");
                  link.href = statusData.download_url;
                  link.download = `translated_${this.selectedFile.name}`;
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }, 500);
              }

              UIManager.showSuccess("Tệp đã được dịch xong!");
              document.getElementById("uploadProgress").style.display = "none";

              // Reload stats and history
              dashboard.stats.loadStats();
              dashboard.history.loadHistory();
            }

            if (statusData.status === "failed") {
              clearInterval(interval);
              UIManager.showError(
                statusData.error || "Đã có lỗi khi xử lý file",
              );
              document.getElementById("uploadProgress").style.display = "none";
            }
          } catch (err) {
            console.error("Status polling error", err);
          }
        }, 1000);
      } else if (data.download_url) {
        // Fallback for immediate synchronous response
        if (data.fallback) {
          UIManager.showError(
            `File was returned as a fallback (${data.fallback_reason}). The file may be plain text.`,
          );
        }
        UIManager.showSuccess("File đã được dịch thành công!");

        // Auto download after a short delay
        setTimeout(() => {
          const link = document.createElement("a");
          link.href = data.download_url;
          link.download = `translated_${this.selectedFile.name}`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }, 1000);

        // Reload stats and history
        dashboard.stats.loadStats();
        dashboard.history.loadHistory();
      }
    } catch (error) {
      console.error("Upload error:", error);
      UIManager.showError(error.message || "Có lỗi khi upload file.");
    } finally {
      // Hide loading state
      uploadBtnText.textContent = "Upload & Dịch";
      uploadBtnLoading.style.display = "none";
      uploadBtn.disabled = false;
    }
  }

  resetUpload() {
    document.getElementById("uploadProgress").style.display = "none";
    document.getElementById("fileInput").value = "";
    document.getElementById("fileInfo").style.display = "none";
    this.selectedFile = null;
  }
}

// Dashboard Stats Manager
class DashboardStatsManager {
  constructor(authManager) {
    this.auth = authManager;
  }

  async loadStats() {
    try {
      // Dev: if token is fake, create mock stats
      const token = localStorage.getItem("token");
      if (token && token.startsWith && token.startsWith("fake")) {
        this.updateStats([
          { created_at: new Date().toISOString(), has_file: false },
        ]);
        return;
      }

      const response = await fetch(
        "/api/translation/history?page=1&per_page=100",
        {
          headers: this.auth.getAuthHeaders(),
        },
      );

      if (!response.ok) throw new Error("Failed to load stats");

      const data = await response.json();
      this.updateStats(data.translations);
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  }

  updateStats(translations) {
    const today = new Date().toDateString();

    let todayCount = 0;
    let documentCount = 0;

    translations.forEach((item) => {
      const itemDate = new Date(item.created_at).toDateString();
      if (itemDate === today) {
        todayCount++;
      }
      if (item.has_file) {
        documentCount++;
      }
    });

    document.getElementById("translationCount").textContent = todayCount;
    document.getElementById("documentCount").textContent = documentCount;
    document.getElementById("usagePercent").textContent =
      Math.min(Math.round((todayCount / 10) * 100), 100) + "%";
  }
}

// Main Dashboard Controller
class DashboardController {
  constructor() {
    this.auth = new AuthManager();
    this.ui = UIManager;
    this.translation = new TranslationManager(this.auth);
    this.history = new HistoryManager(this.auth);
    this.upload = new FileUploadManager(this.auth);
    this.stats = new DashboardStatsManager(this.auth);

    this.init();
  }

  init() {
    // Check authentication first
    if (!this.auth.isAuthenticated()) {
      // Hide the entire dashboard and show login prompt
      this.showLoginRequired();
      return;
    }

    this.setupEventListeners();
    this.loadInitialData();
  }

  showLoginRequired() {
    // Hide main content
    document.querySelector(".dashboard").style.display = "none";
    document.querySelector("nav").style.display = "none";

    // Show login required message
    const loginRequired = document.createElement("div");
    loginRequired.id = "loginRequired";
    loginRequired.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            ">
                <div style="
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    text-align: center;
                    max-width: 400px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                ">
                    <i class="fas fa-lock" style="font-size: 4rem; color: #ffd700; margin-bottom: 20px;"></i>
                    <h2 style="color: white; margin-bottom: 15px;">Yêu cầu đăng nhập</h2>
                    <p style="color: rgba(255, 255, 255, 0.8); margin-bottom: 30px; line-height: 1.6;">
                        Bạn cần đăng nhập để sử dụng tính năng dịch thuật AI.
                    </p>
                    <button onclick="window.location.href='auth.html'" style="
                        background: linear-gradient(45deg, #667eea, #764ba2);
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        border-radius: 10px;
                        font-size: 1rem;
                        font-weight: 600;
                        cursor: pointer;
                        transition: transform 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                        <i class="fas fa-sign-in-alt"></i> Đăng nhập ngay
                    </button>
                </div>
            </div>
        `;
    document.body.appendChild(loginRequired);
  }

  setupEventListeners() {
    try {
      // Logout
      const logoutBtn = document.getElementById("logoutBtn");
      if (logoutBtn) {
        logoutBtn.addEventListener("click", () => this.auth.logout());
      }

      // Login button (in case user gets logged out)
      const loginBtn = document.getElementById("loginBtn");
      if (loginBtn) {
        loginBtn.addEventListener("click", () => {
          window.location.href = "auth.html";
        });
      }

      // User menu
      const userMenuBtn = document.querySelector(".user-menu-btn");
      if (userMenuBtn) {
        userMenuBtn.addEventListener("click", () => this.toggleUserMenu());
      }

      // Close user menu when clicking outside
      document.addEventListener("click", (e) => {
        const userMenu = document.getElementById("userMenu");
        const userMenuBtn = document.querySelector(".user-menu-btn");
        if (
          userMenu &&
          userMenuBtn &&
          !userMenuBtn.contains(e.target) &&
          !userMenu.contains(e.target)
        ) {
          userMenu.classList.remove("show");
        }
      });

      // Tab switching
      const tabButtons = document.querySelectorAll(".tab-btn");
      if (tabButtons && tabButtons.length) {
        tabButtons.forEach((btn) => {
          btn.addEventListener("click", (e) => {
            e.preventDefault();
            // Try to read an explicit target from onclick attribute or data-target
            let onclickAttr = btn.getAttribute("onclick");
            let match =
              onclickAttr && onclickAttr.match(/showTab\(['"]([^'"\)]+)['"]\)/);
            let tabName = match
              ? match[1]
              : btn.dataset.target || btn.getAttribute("data-target");
            if (!tabName && btn.textContent)
              tabName = btn.textContent.toLowerCase().replace(/\s+/g, "");
            this.ui.showTab(tabName);
          });
        });
      }

      // History filter
      const historyFilter = document.getElementById("historyFilter");
      if (historyFilter) {
        historyFilter.addEventListener("change", () =>
          this.history.filterHistory(),
        );
      }

      // Close notification
      const notificationClose = document.querySelector(".notification-close");
      if (notificationClose) {
        notificationClose.addEventListener("click", () =>
          UIManager.hideNotification(),
        );
      }

      // Clear file button
      const clearFileBtn = document.querySelector(
        ".upload-controls .btn-secondary",
      );
      if (clearFileBtn) {
        clearFileBtn.addEventListener("click", () => this.upload.resetUpload());
      }
    } catch (err) {
      console.error("setupEventListeners error:", err);
    }
  }

  toggleUserMenu() {
    const userMenu = document.getElementById("userMenu");
    if (userMenu) {
      userMenu.classList.toggle("show");
    }
  }

  async loadInitialData() {
    const profile = await this.auth.loadUserInfo();
    // If profile not available (invalid token or not logged in), show login prompt
    if (!profile) {
      this.showLoginRequired();
      return;
    }

    await this.stats.loadStats();
    await this.history.loadHistory();

    // Update authentication UI
    this.auth.updateAuthUI();
  }
}

// Global functions for HTML onclick handlers
function showTab(tabName) {
  UIManager.showTab(tabName);
}

function translateText() {
  if (
    typeof dashboard === "undefined" ||
    !dashboard ||
    !dashboard.translation
  ) {
    UIManager.showError("Ứng dụng chưa sẵn sàng. Vui lòng tải lại trang.");
    return;
  }
  dashboard.translation.translateText();
}

function copyResult() {
  dashboard.translation.copyResult();
}

function saveTranslation() {
  dashboard.translation.saveTranslation();
}

function filterHistory() {
  dashboard.history.filterHistory();
}

function changePage(direction) {
  dashboard.history.changePage(direction);
}

function uploadDocument() {
  dashboard.upload.uploadDocument();
}

function closeNotification() {
  UIManager.hideNotification();
}

function clearFile() {
  dashboard.upload.resetUpload();
}

function downloadResult() {
  const outputText = document.getElementById("outputText").textContent;
  const blob = new Blob([outputText], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "translated_text.txt";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
  UIManager.showNotification("Đã tải xuống file kết quả!", "success");
}

function downloadTranslatedFile() {
  // This function is called from the success message
  // The actual download is handled in the uploadDocument method
}

function toggleUserMenu() {
  dashboard.toggleUserMenu();
}

function logout() {
  dashboard.auth.logout();
}

async function deleteHistoryItem(id) {
  if (confirm("Bạn có chắc muốn xóa bản dịch này?")) {
    try {
      const response = await fetch(`/api/history/${id}`, {
        method: "DELETE",
        headers: dashboard.auth.getAuthHeaders(),
      });

      if (response.ok) {
        UIManager.showNotification("Đã xóa bản dịch!", "success");
        dashboard.history.loadHistory();
        dashboard.stats.loadStats();
      } else {
        throw new Error("Delete failed");
      }
    } catch (error) {
      console.error("Error deleting history item:", error);
      UIManager.showNotification("Có lỗi khi xóa bản dịch!", "error");
    }
  }
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener("DOMContentLoaded", () => {
  dashboard = new DashboardController();
});

// Add notification styles dynamically
const style = document.createElement("style");
style.textContent = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        padding: 15px 20px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    }

    .notification.show {
        transform: translateX(0);
    }

    .notification.success {
        border-color: #4CAF50;
    }

    .notification.error {
        border-color: rgba(139,0,0,0.35);
        background: linear-gradient(90deg, #0B0F1A, #6B0000);
        box-shadow: 0 8px 30px rgba(139,0,0,0.12);
    }

    .upload-area.drag-over {
        border-color: #ffd700;
        background: rgba(255, 215, 0, 0.1);
    }
`;
document.head.appendChild(style);
