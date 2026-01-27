// custom_lang_selects.js
// Converts native <select class="lang-select"> into custom dropdowns with dark themed options
(function () {
  function createCustomSelect(native) {
    if (native.dataset._customized) return; // already customized
    native.dataset._customized = "1";

    const wrapper = document.createElement("div");
    wrapper.className = "custom-lang-select-wrapper";

    const display = document.createElement("button");
    display.type = "button";
    display.className = "custom-lang-select";
    display.setAttribute("aria-haspopup", "listbox");
    display.setAttribute("aria-expanded", "false");
    display.tabIndex = 0;
    display.textContent = native.options[native.selectedIndex]
      ? native.options[native.selectedIndex].text
      : native.dataset.placeholder || "Chọn ngôn ngữ";

    const optionsContainer = document.createElement("div");
    optionsContainer.className = "custom-lang-options";
    optionsContainer.setAttribute("role", "listbox");

    // Build options
    Array.from(native.options).forEach((opt, idx) => {
      const o = document.createElement("div");
      o.className = "custom-lang-option";
      o.textContent = opt.textContent;
      o.dataset.value = opt.value;
      o.setAttribute("role", "option");
      if (opt.disabled) o.classList.add("disabled");
      if (opt.selected) o.classList.add("active");
      o.addEventListener("click", (e) => {
        if (opt.disabled) return;
        native.value = opt.value;
        native.dispatchEvent(new Event("change", { bubbles: true }));
        display.textContent = opt.textContent;
        optionsContainer
          .querySelectorAll(".custom-lang-option")
          .forEach((n) => n.classList.remove("active"));
        o.classList.add("active");
        close();
      });
      optionsContainer.appendChild(o);
    });

    function open() {
      optionsContainer.classList.add("open");
      display.setAttribute("aria-expanded", "true");
    }
    function close() {
      optionsContainer.classList.remove("open");
      display.setAttribute("aria-expanded", "false");
    }

    display.addEventListener("click", (e) => {
      e.stopPropagation();
      optionsContainer.classList.contains("open") ? close() : open();
    });
    display.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        open();
        const first = optionsContainer.querySelector(
          ".custom-lang-option:not(.disabled)",
        );
        if (first) first.focus();
      }
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        display.click();
      }
    });

    document.addEventListener("click", () => close());

    // Hide native select but keep it for forms
    native.classList.add("custom-select-native-hidden");
    native.parentNode.insertBefore(wrapper, native);
    wrapper.appendChild(native);
    wrapper.appendChild(display);
    wrapper.appendChild(optionsContainer);
  }

  function init() {
    // Give populate_languages a moment to fill native selects
    setTimeout(() => {
      document
        .querySelectorAll("select.lang-select")
        .forEach((s) => createCustomSelect(s));
    }, 120);
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", init);
  else init();
})();
