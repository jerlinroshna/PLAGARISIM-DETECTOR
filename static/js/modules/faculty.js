// CodeGuard Faculty Workspace & Comparison Diff Module
(function () {
  function init_faculty() {
  // 13. Synchronized scrolling for side-by-side faculty inspection (preserved)
  const studentPane = document.getElementById("student-code-pane");
  const histPane = document.getElementById("hist-code-pane");
  if (studentPane && histPane) {
    let isSyncingLeft = false;
    let isSyncingRight = false;
    studentPane.addEventListener("scroll", function () {
      if (!isSyncingLeft) {
        isSyncingRight = true;
        histPane.scrollTop = this.scrollTop;
      }
      isSyncingLeft = false;
    });
    histPane.addEventListener("scroll", function () {
      if (!isSyncingRight) {
        isSyncingLeft = true;
        studentPane.scrollTop = this.scrollTop;
      }
      isSyncingRight = false;
    });
  }

  // 14. Login Role Selector helper (clean toggle without auto-fill)
  const roleButtons = document.querySelectorAll(".role-toggle-btn");
  const roleInput = document.getElementById("login-role-input");
  if (roleButtons.length > 0 && roleInput) {
    roleButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        roleButtons.forEach(b => b.classList.remove("active"));
        this.classList.add("active");
        const role = this.getAttribute("data-role");
        roleInput.value = role;
      });
    });
  }

  // 19. Faculty Dashboard Workspace Enhancements
  // Collapsible panels toggle handler (Similarity Policy & Analysis Pipeline)
  document.querySelectorAll(".collapse-toggle-btn").forEach(btn => {
    const targetId = btn.getAttribute("aria-controls");
    const target = document.getElementById(targetId);
    
    // Restore saved collapse preference
    try {
      const savedState = localStorage.getItem(`codeguard_collapse_${targetId}`);
      if (savedState === "false" && target) {
        btn.setAttribute("aria-expanded", "false");
        target.classList.add("collapsed");
      }
    } catch (e) {}

    btn.addEventListener("click", function () {
      const isExpanded = this.getAttribute("aria-expanded") === "true";
      const nextState = !isExpanded;
      this.setAttribute("aria-expanded", String(nextState));
      if (target) {
        if (nextState) {
          target.classList.remove("collapsed");
        } else {
          target.classList.add("collapsed");
        }
      }
      try {
        localStorage.setItem(`codeguard_collapse_${targetId}`, String(nextState));
      } catch (e) {}
    });
  });

  // System Operational Health Monitor
  // TODO: connect API - Replace with live monitoring endpoint (e.g. /api/system/health or /faculty/health)
  function initSystemHealthMonitoring() {
    const pill = document.getElementById("systemStatusPill");
    const statusText = document.getElementById("systemStatusText");
    if (!pill || !statusText) return;

    // Default to operational; can be updated dynamically via window.SYSTEM_STATUS or API callback
    function setSystemStatus(status) {
      pill.classList.remove("status-operational", "status-degraded", "status-outage");
      if (status === "degraded") {
        pill.classList.add("status-degraded");
        statusText.textContent = "System Degraded";
      } else if (status === "outage") {
        pill.classList.add("status-outage");
        statusText.textContent = "Service Outage";
      } else {
        pill.classList.add("status-operational");
        statusText.textContent = "System Operational";
      }
    }

    // Expose hook on window for testability or websocket/API integration
    window.updateSystemHealth = setSystemStatus;
    if (window.CODGUARD_SYSTEM_STATUS) {
      setSystemStatus(window.CODGUARD_SYSTEM_STATUS);
    }
  }
  initSystemHealthMonitoring();

  // Quick live-filter for Faculty Dashboard Recent Submissions Table
  const facultyTableSearch = document.getElementById("globalSearchInput");
  const facultySubRows = document.querySelectorAll(".faculty-sub-row");
  if (facultyTableSearch && facultySubRows.length > 0) {
    facultyTableSearch.addEventListener("input", function () {
      const q = this.value.toLowerCase().trim();
      facultySubRows.forEach(row => {
        const text = (row.textContent || "").toLowerCase();
        row.style.display = (!q || text.includes(q)) ? "" : "none";
      });
    });
  }

  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init_faculty);
  } else {
    init_faculty();
  }
})();
