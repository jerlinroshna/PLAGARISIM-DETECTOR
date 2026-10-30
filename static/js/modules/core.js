// CodeGuard Core Navigation, Theme & Global Shortcuts Module
document.addEventListener("DOMContentLoaded", function () {
  // 1. Mobile Sidebar Drawer & Backdrop
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");
  const sidebar = document.getElementById("appSidebar");
  const sidebarBackdrop = document.getElementById("sidebarBackdrop");
  const sidebarCloseBtn = document.getElementById("sidebarCloseBtn");

  function openSidebar() {
    if (sidebar) sidebar.classList.add("mobile-open");
    if (sidebarBackdrop) sidebarBackdrop.classList.add("active");
    document.body.classList.add("sidebar-open");
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove("mobile-open");
    if (sidebarBackdrop) sidebarBackdrop.classList.remove("active");
    document.body.classList.remove("sidebar-open");
  }

  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      if (sidebar && sidebar.classList.contains("mobile-open")) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener("click", closeSidebar);
  }

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener("click", closeSidebar);
  }

  // Auto-close drawer when clicking any nav link on mobile screens
  if (sidebar) {
    sidebar.querySelectorAll(".nav-item").forEach(link => {
      link.addEventListener("click", function () {
        if (window.innerWidth <= 1024) {
          closeSidebar();
        }
      });
    });
  }

  // 1b. Desktop Mini Sidebar Toggle & Persistence
  try {
    const savedMini = localStorage.getItem("codeguard_sidebar_mini");
    if (savedMini === "true" && sidebar) {
      sidebar.classList.add("sidebar-student-mini");
    }
  } catch (err) {
    // Local storage disabled or error
  }

  // 1c. Theme Switcher (Cycle: light, dark, system - Phase A.4 & Phase B)
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  function applyTheme(theme) {
    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
      document.body.classList.add("theme-dark");
      if (themeToggleBtn) {
        themeToggleBtn.setAttribute("title", "Active: Dark Mode (Click to cycle)");
        themeToggleBtn.setAttribute("aria-label", "Toggle theme: Dark mode active");
      }
    } else if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
      document.body.classList.remove("theme-dark");
      if (themeToggleBtn) {
        themeToggleBtn.setAttribute("title", "Active: Light Mode (Click to cycle)");
        themeToggleBtn.setAttribute("aria-label", "Toggle theme: Light mode active");
      }
    } else {
      // System mode
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      if (prefersDark) {
        document.documentElement.setAttribute("data-theme", "dark");
        document.body.classList.add("theme-dark");
      } else {
        document.documentElement.setAttribute("data-theme", "light");
        document.body.classList.remove("theme-dark");
      }
      if (themeToggleBtn) {
        themeToggleBtn.setAttribute("title", "Active: System Mode (Click to cycle)");
        themeToggleBtn.setAttribute("aria-label", "Toggle theme: System preference active");
      }
    }
  }

  let currentTheme = "light";
  try {
    currentTheme = localStorage.getItem("codeguard_theme") || "light";
  } catch (e) {
    currentTheme = "light";
  }
  applyTheme(currentTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", function () {
      let nextTheme = "light";
      if (currentTheme === "light") nextTheme = "dark";
      else if (currentTheme === "dark") nextTheme = "system";
      else nextTheme = "light";

      currentTheme = nextTheme;
      try {
        localStorage.setItem("codeguard_theme", nextTheme);
      } catch (e) {}
      applyTheme(nextTheme);
    });
  }

  // 1d. Global Keyboard Shortcuts: Ctrl+K / Cmd+K to focus Search, Esc to close popovers
  const searchInput = document.getElementById("globalSearchInput");
  const searchPill = document.getElementById("topbarSearchPill");
  const notifMenu = document.getElementById("notifDropdownMenu");
  const userMenu = document.getElementById("userProfileMenu");

  const isMac = /(Mac|iPhone|iPod|iPad)/i.test(navigator.platform || navigator.userAgent);
  const kbdChip = document.getElementById("searchKbdChip");
  if (kbdChip) {
    kbdChip.textContent = isMac ? "⌘ K" : "Ctrl K";
    kbdChip.title = `Press ${isMac ? "⌘K" : "Ctrl+K"} to search`;
  }

  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K")) {
      e.preventDefault();
      if (searchPill && window.innerWidth <= 768) {
        searchPill.classList.add("mobile-expanded");
      }
      if (searchInput) {
        searchInput.focus();
        searchInput.select();
      }
    } else if (e.key === "Escape") {
      if (notifMenu) notifMenu.classList.remove("active");
      if (userMenu) userMenu.classList.remove("active");
      if (searchPill) searchPill.classList.remove("mobile-expanded");
      if (searchInput && document.activeElement === searchInput) {
        searchInput.blur();
      }
    }
  });

  if (searchPill) {
    searchPill.addEventListener("click", function (e) {
      if (window.innerWidth <= 768) {
        searchPill.classList.add("mobile-expanded");
        if (searchInput) searchInput.focus();
      }
    });
  }

  // 2. Notification Bell & User Dropdown Popovers
  const notifBtn = document.getElementById("notifBellBtn");
  if (notifBtn && notifMenu) {
    notifBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      notifMenu.classList.toggle("active");
      if (userMenu) userMenu.classList.remove("active");
    });
  }

  const userBtn = document.getElementById("userProfileBtn");
  if (userBtn && userMenu) {
    userBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      userMenu.classList.toggle("active");
      if (notifMenu) notifMenu.classList.remove("active");
    });
  }

  document.addEventListener("click", function (e) {
    if (notifMenu && !notifMenu.contains(e.target) && notifBtn && !notifBtn.contains(e.target)) {
      notifMenu.classList.remove("active");
    }
    if (userMenu && !userMenu.contains(e.target) && userBtn && !userBtn.contains(e.target)) {
      userMenu.classList.remove("active");
    }
    if (searchPill && !searchPill.contains(e.target)) {
      searchPill.classList.remove("mobile-expanded");
    }
  });

  // 15. Dynamic Floating Tooltip for Student Mini Sidebar (Immune to overflow clipping)
  const miniSidebar = document.querySelector(".sidebar-student-mini, .sidebar");
  if (miniSidebar) {
    let floatingTooltip = document.getElementById("sidebar-floating-tooltip");
    if (!floatingTooltip) {
      floatingTooltip = document.createElement("div");
      floatingTooltip.id = "sidebar-floating-tooltip";
      floatingTooltip.className = "sidebar-floating-tooltip";
      document.body.appendChild(floatingTooltip);
    }

    const navItems = miniSidebar.querySelectorAll(".nav-item");
    navItems.forEach(function (item) {
      const tooltipText = item.getAttribute("data-tooltip") || 
                          item.getAttribute("title") ||
                          (item.querySelector(".nav-label") ? item.querySelector(".nav-label").textContent.trim() : "");
      if (!tooltipText) return;

      // Remove title to prevent duplicate native browser tooltip
      item.removeAttribute("title");

      item.addEventListener("mouseenter", function () {
        if (window.innerWidth <= 1024) return;
        const rect = item.getBoundingClientRect();
        floatingTooltip.textContent = tooltipText;
        floatingTooltip.style.top = (rect.top + rect.height / 2) + "px";
        floatingTooltip.style.left = (rect.right + 12) + "px";
        floatingTooltip.classList.add("visible");
      });

      item.addEventListener("mouseleave", function () {
        floatingTooltip.classList.remove("visible");
      });

      item.addEventListener("click", function () {
        floatingTooltip.classList.remove("visible");
      });
    });

    window.addEventListener("scroll", function () {
      if (floatingTooltip) floatingTooltip.classList.remove("visible");
    }, true);

    window.addEventListener("resize", function () {
      if (floatingTooltip) floatingTooltip.classList.remove("visible");
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // 20. Expandable Sidebar Toggle with LocalStorage Persistence
  // ─────────────────────────────────────────────────────────────────────────
  const sidebarExpandBtn = document.getElementById("sidebarToggleBtn");
  if (sidebar && sidebarExpandBtn) {
    // Restore saved expansion state
    try {
      const isExpanded = localStorage.getItem("codeguard_sidebar_expanded") === "true";
      if (isExpanded) {
        sidebar.classList.add("sidebar-expanded");
        sidebarExpandBtn.setAttribute("title", "Collapse sidebar");
      }
    } catch (_) {}

    sidebarExpandBtn.addEventListener("click", function () {
      const expanded = sidebar.classList.toggle("sidebar-expanded");
      sidebarExpandBtn.setAttribute("title", expanded ? "Collapse sidebar" : "Expand sidebar");
      try {
        localStorage.setItem("codeguard_sidebar_expanded", String(expanded));
      } catch (_) {}
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // 21. Accessible Logout Confirmation Dialog
  // ─────────────────────────────────────────────────────────────────────────
  const logoutLink = document.getElementById("sidebarLogoutLink");
  const logoutModal = document.getElementById("logoutConfirmModal");
  const logoutModalCancel = document.getElementById("btnLogoutModalCancel");

  if (logoutLink && logoutModal) {
    logoutLink.addEventListener("click", function (e) {
      e.preventDefault();
      if (typeof logoutModal.showModal === "function") {
        logoutModal.showModal();
      } else {
        if (confirm("Are you sure you want to sign out of the portal?")) {
          window.location.href = logoutLink.href;
        }
      }
    });

    if (logoutModalCancel) {
      logoutModalCancel.addEventListener("click", function () {
        logoutModal.close();
      });
    }

    // Close on backdrop click
    logoutModal.addEventListener("click", function (e) {
      if (e.target === logoutModal) logoutModal.close();
    });
  }

});
