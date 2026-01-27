// about.js - About page JavaScript
document.addEventListener("DOMContentLoaded", function () {
  initializeAboutPage();
});

function initializeAboutPage() {
  setupAnimations();
  setupStatsCounter();
  setupTeamCards();
}

function setupAnimations() {
  // Intersection Observer for fade-in animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("animate-in");
      }
    });
  }, observerOptions);

  // Observe elements for animation
  document
    .querySelectorAll(
      ".story-text, .story-image, .mission-card, .vision-card, .values-card, .team-member, .stat-item",
    )
    .forEach((element) => {
      observer.observe(element);
    });
}

function setupStatsCounter() {
  const stats = document.querySelectorAll(".stat-number");

  const counterObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const target = parseFloat(entry.target.dataset.target);
          animateCounter(entry.target, 0, target, 2000);
          counterObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.5 },
  );

  stats.forEach((stat) => {
    counterObserver.observe(stat);
  });
}

function animateCounter(element, start, end, duration) {
  const startTime = performance.now();
  const isFloat = end % 1 !== 0;

  function updateCounter(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Easing function for smooth animation
    const easeOutQuart = 1 - Math.pow(1 - progress, 4);
    const current = start + (end - start) * easeOutQuart;

    if (isFloat) {
      element.textContent = current.toFixed(1);
    } else {
      element.textContent = Math.floor(current);
    }

    if (progress < 1) {
      requestAnimationFrame(updateCounter);
    } else {
      element.textContent = isFloat ? end.toFixed(1) : end;
    }
  }

  requestAnimationFrame(updateCounter);
}

function setupTeamCards() {
  const teamMembers = document.querySelectorAll(".team-member");

  teamMembers.forEach((member) => {
    // Add hover effect
    member.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-10px)";
    });

    member.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0)";
    });

    // Add click effect for social links
    const socialLinks = member.querySelectorAll(".member-social a");
    socialLinks.forEach((link) => {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        // Here you would open social media links
        console.log("Opening social link:", this.href);
        // For demo purposes, show a message
        showSocialMessage(this.querySelector("i").className);
      });
    });
  });
}

function showSocialMessage(iconClass) {
  const platform = getPlatformFromIcon(iconClass);
  showNotification(`Đang mở ${platform}...`, "info");
}

function getPlatformFromIcon(iconClass) {
  if (iconClass.includes("linkedin")) return "LinkedIn";
  if (iconClass.includes("twitter")) return "Twitter";
  if (iconClass.includes("github")) return "GitHub";
  if (iconClass.includes("dribbble")) return "Dribbble";
  if (iconClass.includes("behance")) return "Behance";
  return "mạng xã hội";
}

function showNotification(message, type = "info") {
  // Remove existing notifications
  const existingNotifications = document.querySelectorAll(".page-notification");
  existingNotifications.forEach((notification) => notification.remove());

  // Create new notification
  const notification = document.createElement("div");
  notification.className = `page-notification ${type}`;
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

// Add custom styles for about page
const aboutStyle = document.createElement("style");
aboutStyle.textContent = `
    /* Animation styles */
    .story-text, .story-image, .mission-card, .vision-card, .values-card, .team-member, .stat-item {
        opacity: 0;
        transform: translateY(30px);
        transition: opacity 0.8s ease, transform 0.8s ease;
    }

    .story-text.animate-in, .story-image.animate-in,
    .mission-card.animate-in, .vision-card.animate-in,
    .values-card.animate-in, .team-member.animate-in,
    .stat-item.animate-in {
        opacity: 1;
        transform: translateY(0);
    }

    /* Team member hover effects */
    .team-member {
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        cursor: pointer;
    }

    .team-member:hover {
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
    }

    .member-avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 2rem;
        margin: 0 auto 15px;
    }

    .member-social {
        margin-top: 15px;
    }

    .member-social a {
        display: inline-block;
        margin: 0 5px;
        color: rgba(255, 255, 255, 0.7);
        transition: color 0.3s ease;
    }

    .member-social a:hover {
        color: white;
    }

    /* Stats styling */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 30px;
        margin-top: 50px;
    }

    .stat-item {
        text-align: center;
        padding: 30px;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .stat-number {
        font-size: 3rem;
        font-weight: bold;
        color: #ffd700;
        margin-bottom: 10px;
        display: block;
    }

    .stat-label {
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.9);
        font-weight: 500;
    }

    /* Notification styles */
    .page-notification {
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
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .page-notification.show {
        transform: translateX(0);
    }

    .page-notification.success {
        border-color: #4CAF50;
    }

    .page-notification.error {
        border-color: #f44336;
    }

    .page-notification.info {
        border-color: #2196F3;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }

        .stat-number {
            font-size: 2.5rem;
        }
    }

    @media (max-width: 480px) {
        .stats-grid {
            grid-template-columns: 1fr;
        }

        .stat-number {
            font-size: 2rem;
        }
    }
`;
document.head.appendChild(aboutStyle);
