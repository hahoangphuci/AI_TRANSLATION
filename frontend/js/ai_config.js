// Cấu hình AI – values thật lấy từ /api/ai/config (backend .env). API key KHÔNG đặt ở frontend.
window.AI_CONFIG = window.AI_CONFIG || {
  API_KEY: null, // Giữ null – key chỉ ở backend (.env OPENROUTER_API_KEY)
  PROVIDER: "openrouter",
  MODEL: "openai/gpt-4o-mini",
  AVAILABLE_MODELS: [
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-pro",
    "anthropic/claude-3-haiku",
    "meta-llama/llama-3.1-8b-instruct:free",
  ],
  ENDPOINTS: {
    chat: "https://openrouter.ai/api/v1/chat/completions",
    models: "https://openrouter.ai/api/v1/models",
  },
  HEADERS: {
    "HTTP-Referer": "https://codequest-ai.vercel.app",
    "X-Title": "CodeQuest AI Learning Platform",
  },
  hasApiKey: false, // Sẽ thành true khi /api/ai/config trả về has_api_key (backend đã cấu hình OPENROUTER_API_KEY)
};

// Fetch actual server-side config to know if API key exists and to override values
fetch("/api/ai/config")
  .then((r) => (r.ok ? r.json() : null))
  .then((cfg) => {
    if (!cfg) return;
    window.AI_CONFIG.PROVIDER = cfg.provider || window.AI_CONFIG.PROVIDER;
    window.AI_CONFIG.MODEL = cfg.model || window.AI_CONFIG.MODEL;
    if (cfg.available_models && typeof cfg.available_models === "string") {
      window.AI_CONFIG.AVAILABLE_MODELS = cfg.available_models
        .split(",")
        .map((s) => s.trim());
    }
    if (cfg.endpoints) window.AI_CONFIG.ENDPOINTS = cfg.endpoints;
    if (cfg.headers) window.AI_CONFIG.HEADERS = cfg.headers;
    window.AI_CONFIG.hasApiKey = !!cfg.has_api_key;
  })
  .catch((err) => {
    console.warn("Could not fetch AI config:", err);
  });
