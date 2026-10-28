// Source-Code Plagiarism Detector - Student Portal & College Portal Interactions

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

  // 3. Tab switching (e.g. Upload File vs Paste Code)
  const tabButtons = document.querySelectorAll(".portal-tab-btn");
  tabButtons.forEach(btn => {
    btn.addEventListener("click", function () {
      const targetId = this.getAttribute("data-tab-target");
      if (!targetId) return;

      const parent = this.closest(".portal-tabs-container") || document;
      parent.querySelectorAll(".portal-tab-btn").forEach(b => b.classList.remove("active"));
      parent.querySelectorAll(".portal-tab-content").forEach(c => c.style.display = "none");

      this.classList.add("active");
      const target = document.getElementById(targetId);
      if (target) target.style.display = "block";
    });
  });

  // 4. File Drag & Drop and Preview
  const dropzone = document.getElementById("uploadDropzone");
  const fileInput = document.getElementById("code_file");
  const filePreview = document.getElementById("filePreviewInfo");
  const langSelect = document.getElementById("programming_language");

  function handleFileSelected(file) {
    if (!file) return;
    const filename = file.name.toLowerCase();
    let detected = "";

    if (filename.endsWith(".py")) detected = "python";
    else if (filename.endsWith(".java")) detected = "java";
    else if (filename.endsWith(".c")) detected = "c";
    else if (filename.endsWith(".cpp") || filename.endsWith(".cc") || filename.endsWith(".cxx")) detected = "cpp";
    else if (filename.endsWith(".js")) detected = "javascript";

    if (detected && langSelect) {
      for (let i = 0; i < langSelect.options.length; i++) {
        if (langSelect.options[i].value === detected) {
          langSelect.selectedIndex = i;
          break;
        }
      }
    }

    if (filePreview) {
      const sizeKb = (file.size / 1024).toFixed(1);
      filePreview.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; margin-top: 12px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.2rem;">&#128196;</span>
            <div>
              <div style="font-weight: 600; font-size: 0.86rem; color: #166534;">${file.name}</div>
              <div style="font-size: 0.74rem; color: #15803d;">${sizeKb} KB &bull; Language: ${detected ? detected.toUpperCase() : 'Manual select'}</div>
            </div>
          </div>
          <span class="badge" style="background: #dcfce7; color: #166534; font-weight: 600;">File Ready</span>
        </div>
      `;
      filePreview.style.display = "block";
    }

    updateChecklist();
  }

  if (fileInput) {
    fileInput.addEventListener("change", function () {
      if (this.files && this.files.length > 0) {
        handleFileSelected(this.files[0]);
      }
    });
  }

  if (dropzone && fileInput) {
    ["dragenter", "dragover"].forEach(eventName => {
      dropzone.addEventListener(eventName, e => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });
    });
    ["dragleave", "drop"].forEach(eventName => {
      dropzone.addEventListener(eventName, e => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
      });
    });
    dropzone.addEventListener("drop", e => {
      if (e.dataTransfer && e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelected(fileInput.files[0]);
      }
    });
    dropzone.addEventListener("click", () => fileInput.click());
  }

  // 5. Code editor statistics and Tab key handling
  const codeTextarea = document.getElementById("code_text");
  const statLines = document.getElementById("stat-lines");
  const statChars = document.getElementById("stat-chars");
  const statFuncs = document.getElementById("stat-funcs");
  const statComments = document.getElementById("stat-comments");

  function calculateCodeStats() {
    if (!codeTextarea) return;
    const text = codeTextarea.value;
    const lines = text ? text.split("\n").length : 0;
    const chars = text.length;

    // Detect function patterns statically across languages (e.g. def foo, function bar, void foo(), int main())
    const funcRegex = /(def\s+[a-zA-Z0-9_]+|function\s+[a-zA-Z0-9_]+|[a-zA-Z0-9_]+\s*\([^)]*\)\s*\{|void\s+[a-zA-Z0-9_]+|int\s+[a-zA-Z0-9_]+)/g;
    const funcMatches = text.match(funcRegex);
    const funcs = funcMatches ? funcMatches.length : 0;

    // Detect comments statically
    const commentRegex = /(\/\/.*|#.*|\/\*[\s\S]*?\*\/)/g;
    const commentMatches = text.match(commentRegex);
    const comments = commentMatches ? commentMatches.length : 0;

    if (statLines) statLines.textContent = lines;
    if (statChars) statChars.textContent = chars;
    if (statFuncs) statFuncs.textContent = funcs;
    if (statComments) statComments.textContent = comments;

    updateChecklist();
  }

  if (codeTextarea) {
    codeTextarea.addEventListener("input", calculateCodeStats);
    codeTextarea.addEventListener("keydown", function (e) {
      if (e.key === "Tab") {
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value = this.value.substring(0, start) + "    " + this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;
        calculateCodeStats();
      }
    });
  }

  // 6. Live Static Validation Checklist & Submit enabler
  const asgnSelect = document.getElementById("assignment_id");
  const chkAsgn = document.getElementById("chk-asgn");
  const chkLang = document.getElementById("chk-lang");
  const chkCode = document.getElementById("chk-code");
  const chkSize = document.getElementById("chk-size");

  const chkPolicy1 = document.getElementById("policy-chk-1");
  const chkPolicy2 = document.getElementById("policy-chk-2");
  const chkPolicy3 = document.getElementById("policy-chk-3");
  const submitBtn = document.getElementById("submitForAnalysisBtn");

  function updateChecklist() {
    let hasAsgn = false;
    let hasLang = false;
    let hasCode = false;
    let validSize = true;

    if (asgnSelect && asgnSelect.value) hasAsgn = true;
    if (langSelect && langSelect.value && langSelect.value !== "auto") hasLang = true;

    if (fileInput && fileInput.files && fileInput.files.length > 0) {
      hasCode = true;
      if (fileInput.files[0].size > 5 * 1024 * 1024) validSize = false;
    } else if (codeTextarea && codeTextarea.value.trim().length > 0) {
      hasCode = true;
    }

    if (chkAsgn) setCheckStatus(chkAsgn, hasAsgn);
    if (chkLang) setCheckStatus(chkLang, hasLang);
    if (chkCode) setCheckStatus(chkCode, hasCode);
    if (chkSize) setCheckStatus(chkSize, validSize);

    const allPolicies = chkPolicy1 && chkPolicy2 && chkPolicy3 && chkPolicy1.checked && chkPolicy2.checked && chkPolicy3.checked;

    if (submitBtn) {
      if (hasAsgn && hasLang && hasCode && validSize && allPolicies) {
        submitBtn.removeAttribute("disabled");
        submitBtn.style.opacity = "1";
        submitBtn.style.cursor = "pointer";
      } else {
        submitBtn.setAttribute("disabled", "true");
        submitBtn.style.opacity = "0.6";
        submitBtn.style.cursor = "not-allowed";
      }
    }
  }

  function setCheckStatus(el, isValid) {
    if (isValid) {
      el.textContent = "✓";
      el.style.color = "#10b981";
      el.style.fontWeight = "700";
    } else {
      el.textContent = "○";
      el.style.color = "#94a3b8";
      el.style.fontWeight = "normal";
    }
  }

  if (asgnSelect) asgnSelect.addEventListener("change", function () {
    // Show assignment metadata card if present
    const selOpt = asgnSelect.options[asgnSelect.selectedIndex];
    const infoCard = document.getElementById("selectedAsgnInfo");
    if (infoCard && selOpt.value) {
      const allowed = selOpt.getAttribute("data-allowed") || "Any";
      const deadline = selOpt.getAttribute("data-deadline") || "No explicit deadline";
      const subj = selOpt.getAttribute("data-subject") || "General";
      infoCard.innerHTML = `
        <div style="font-weight: 600; color: #1e3a8a; margin-bottom: 2px;">${selOpt.text}</div>
        <div style="font-size: 0.78rem; color: #475569;">
          Subject: <strong>${subj}</strong> &bull; Deadline: <strong>${deadline}</strong> &bull; Allowed: <strong>${allowed.toUpperCase()}</strong>
        </div>
      `;
      infoCard.style.display = "block";
    }
    updateChecklist();
  });
  if (langSelect) langSelect.addEventListener("change", updateChecklist);
  if (chkPolicy1) chkPolicy1.addEventListener("change", updateChecklist);
  if (chkPolicy2) chkPolicy2.addEventListener("change", updateChecklist);
  if (chkPolicy3) chkPolicy3.addEventListener("change", updateChecklist);

  // 7. Ready-to-Submit Confirmation Modal
  const confirmModal = document.getElementById("confirmSubmitModal");
  const cancelSubmitBtn = document.getElementById("cancelSubmitModalBtn");
  const proceedSubmitBtn = document.getElementById("proceedSubmitBtn");
  const submissionForm = document.getElementById("submissionForm");

  if (submitBtn && confirmModal && submissionForm) {
    submitBtn.addEventListener("click", function (e) {
      e.preventDefault();
      // Populate modal summary
      const mAsgn = document.getElementById("modalAsgnName");
      const mLang = document.getElementById("modalLangName");
      const mFile = document.getElementById("modalFileName");

      if (mAsgn && asgnSelect) mAsgn.textContent = asgnSelect.options[asgnSelect.selectedIndex].text;
      if (mLang && langSelect) mLang.textContent = langSelect.options[langSelect.selectedIndex].text;
      if (mFile) {
        if (fileInput && fileInput.files.length > 0) {
          mFile.textContent = fileInput.files[0].name;
        } else {
          mFile.textContent = "Pasted Editor Code";
        }
      }

      confirmModal.classList.add("active");
    });
  }

  if (cancelSubmitBtn && confirmModal) {
    cancelSubmitBtn.addEventListener("click", function () {
      confirmModal.classList.remove("active");
    });
  }

  if (proceedSubmitBtn && submissionForm) {
    proceedSubmitBtn.addEventListener("click", function () {
      // Show progress state
      const progressContainer = document.getElementById("submissionProcessingCard");
      if (progressContainer) {
        confirmModal.classList.remove("active");
        progressContainer.style.display = "block";
        progressContainer.scrollIntoView({ behavior: "smooth" });
      }
      setTimeout(() => {
        submissionForm.submit();
      }, 400);
    });
  }

  // 8. Copy Code Button
  const copyBtn = document.getElementById("copyCodeBtn");
  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      const codeLines = document.querySelectorAll(".code-line-text");
      let fullCode = "";
      codeLines.forEach(l => fullCode += l.textContent + "\n");

      if (!fullCode) {
        const pane = document.querySelector(".pane-body");
        if (pane) fullCode = pane.innerText;
      }

      if (navigator.clipboard) {
        navigator.clipboard.writeText(fullCode).then(() => {
          const originalText = copyBtn.innerHTML;
          copyBtn.innerHTML = `<span>&#10003; Copied!</span>`;
          setTimeout(() => copyBtn.innerHTML = originalText, 2000);
        });
      }
    });
  }

  // 9. Fullscreen Code Viewer Toggle
  const fsBtn = document.getElementById("fullscreenCodeBtn");
  const codeBox = document.querySelector(".modern-code-container");
  if (fsBtn && codeBox) {
    fsBtn.addEventListener("click", function () {
      if (!document.fullscreenElement) {
        codeBox.requestFullscreen().catch(err => alert(`Error: ${err.message}`));
      } else {
        document.exitFullscreen();
      }
    });
  }

  // 10. Code Line Search
  const codeSearch = document.getElementById("codeLineSearch");
  if (codeSearch) {
    codeSearch.addEventListener("input", function () {
      const query = this.value.toLowerCase();
      const rows = document.querySelectorAll(".code-line-row");
      rows.forEach(r => {
        const text = r.querySelector(".code-line-text");
        if (text) {
          if (!query || text.textContent.toLowerCase().includes(query)) {
            r.style.display = "flex";
          } else {
            r.style.display = "none";
          }
        }
      });
    });
  }

  // 11. Clarification Request Modal & Character Counter
  const openClarifyBtn = document.getElementById("openClarificationModalBtn");
  const clarifyModal = document.getElementById("clarificationModal");
  const closeClarifyBtn = document.getElementById("closeClarificationModalBtn");
  const clarifyText = document.getElementById("clarificationStatement");
  const clarifyCount = document.getElementById("clarificationCharCount");

  if (openClarifyBtn && clarifyModal) {
    openClarifyBtn.addEventListener("click", function () {
      clarifyModal.classList.add("active");
    });
  }
  if (closeClarifyBtn && clarifyModal) {
    closeClarifyBtn.addEventListener("click", function () {
      clarifyModal.classList.remove("active");
    });
  }
  if (clarifyText && clarifyCount) {
    clarifyText.addEventListener("input", function () {
      clarifyCount.textContent = this.value.length;
    });
  }

  // 12. Accordion Toggle for Structural Comparison Explanation
  const accordionHeader = document.getElementById("accordionExplanationHeader");
  const accordionBody = document.getElementById("accordionExplanationBody");
  const accordionIcon = document.getElementById("accordionExplanationIcon");
  if (accordionHeader && accordionBody) {
    accordionHeader.addEventListener("click", function () {
      const isOpen = accordionBody.style.display === "block";
      accordionBody.style.display = isOpen ? "none" : "block";
      if (accordionIcon) accordionIcon.textContent = isOpen ? "▼" : "▲";
    });
  }

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

  // 15. Dynamic Floating Tooltip for Student Mini Sidebar (Immune to overflow clipping)
  const miniSidebar = document.querySelector(".sidebar-student-mini");
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

  // 17. Student Dashboard Controller
  const studentDashboard = document.getElementById("studentDashboardApp");
  if (studentDashboard) {
    // 17a. Time-based dynamic greeting
    const greetingText = document.getElementById("heroGreetingText");
    if (greetingText) {
      const hour = new Date().getHours();
      if (hour < 12) {
        greetingText.textContent = "Good Morning";
      } else if (hour < 17) {
        greetingText.textContent = "Good Afternoon";
      } else {
        greetingText.textContent = "Good Evening";
      }
    }

    // 17b. Deterministic Daily Academic Integrity Tip (rotates daily client-side)
    const integrityTips = [
      "Original algorithm design reflects genuine learning. Build logic independently and cite authorized references cleanly.",
      "Variable renaming and statement reordering does not alter AST structure or bypass semantic detection.",
      "Discuss high-level concepts with peers, but always write your implementation and logic independently.",
      "Using external libraries or snippets? Always add inline attribution comments specifying the original author and source.",
      "Drafting pseudocode before typing code helps develop distinct algorithmic structure and clarity.",
      "Reviewing fellow students' code solutions before finishing your own can lead to unintended structural plagiarism.",
      "Clean, modular code with descriptive function comments highlights authentic problem-solving.",
      "When using AI assistance for debugging, ensure you understand and re-implement every algorithm logic step.",
      "Consistent coding style and self-authored helper functions provide strong signals of independent authorship.",
      "Academic integrity protects your engineering growth. Master the data structures by building them from scratch."
    ];
    const tipTextEl = document.getElementById("heroIntegrityTipText");
    if (tipTextEl) {
      const today = new Date();
      const startOfYear = new Date(today.getFullYear(), 0, 0);
      const dayOfYear = Math.floor((today - startOfYear) / (1000 * 60 * 60 * 24));
      tipTextEl.textContent = integrityTips[dayOfYear % integrityTips.length];
    }

    // 17c. Animated metric counters (respects prefers-reduced-motion)
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const metricNumbers = document.querySelectorAll(".metric-number[data-target]");
    if (!prefersReducedMotion) {
      metricNumbers.forEach(el => {
        const target = parseInt(el.getAttribute("data-target"), 10) || 0;
        if (target === 0) return;
        let current = 0;
        const duration = 600;
        const stepTime = Math.max(16, Math.floor(duration / target));
        const timer = setInterval(() => {
          current += Math.ceil(target / (duration / stepTime));
          if (current >= target) {
            el.textContent = target;
            clearInterval(timer);
          } else {
            el.textContent = current;
          }
        }, stepTime);
      });

      // Animate Health Score Gauge Bar & Count-up
      const healthScoreVal = document.querySelector(".health-score-val[data-target]");
      const gaugeBar = document.querySelector(".health-gauge-svg .gauge-bar");
      if (healthScoreVal && gaugeBar) {
        const targetScore = parseInt(healthScoreVal.getAttribute("data-target"), 10) || 0;
        const fullCircumference = 314.16;
        const targetOffset = (314.16 - (targetScore / 100 * 314.16)).toFixed(1);
        gaugeBar.style.strokeDashoffset = fullCircumference;
        setTimeout(() => {
          gaugeBar.style.transition = "stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1)";
          gaugeBar.style.strokeDashoffset = targetOffset;
        }, 150);
      }
    }

    // 17d. Dismissible Flagged Alert Banner
    const flaggedBanner = document.getElementById("flaggedAlertBanner");
    const dismissFlaggedBtn = document.getElementById("dismissFlaggedBtn");
    if (flaggedBanner && dismissFlaggedBtn) {
      if (sessionStorage.getItem("codeguard-flagged-dismissed") === "true") {
        flaggedBanner.style.display = "none";
      }
      dismissFlaggedBtn.addEventListener("click", function () {
        flaggedBanner.style.opacity = "0";
        setTimeout(() => {
          flaggedBanner.style.display = "none";
          sessionStorage.setItem("codeguard-flagged-dismissed", "true");
        }, 200);
      });
    }

    // 17e. SVG Donut Chart Calculation & Animation
    const donutSvg = document.querySelector(".donut-svg");
    if (donutSvg) {
      const circumference = 439.82; // 2 * PI * 70
      const segments = [
        document.querySelector(".segment-low"),
        document.querySelector(".segment-medium"),
        document.querySelector(".segment-high")
      ].filter(Boolean);

      let accumulatedOffset = 0;
      segments.forEach(seg => {
        const pct = parseFloat(seg.getAttribute("data-percent")) || 0;
        const strokeLength = (pct / 100) * circumference;
        seg.style.strokeDasharray = `${strokeLength} ${circumference - strokeLength}`;
        seg.style.strokeDashoffset = -accumulatedOffset;
        accumulatedOffset += strokeLength;

        // Hover tooltip
        const tooltip = document.getElementById("donutTooltip");
        if (tooltip) {
          seg.addEventListener("mouseenter", function (e) {
            const label = this.getAttribute("data-label");
            const cnt = this.getAttribute("data-count");
            const p = this.getAttribute("data-percent");
            tooltip.textContent = `${label}: ${cnt} (${p}%)`;
            tooltip.style.display = "block";
          });
          seg.addEventListener("mousemove", function (e) {
            const wrapper = document.querySelector(".donut-svg-wrapper");
            if (wrapper) {
              const rect = wrapper.getBoundingClientRect();
              tooltip.style.left = (e.clientX - rect.left + 10) + "px";
              tooltip.style.top = (e.clientY - rect.top - 20) + "px";
            }
          });
          seg.addEventListener("mouseleave", function () {
            tooltip.style.display = "none";
          });
        }
      });
    }

    // 17f. Activity Bar Chart Toggle (7 Days vs 6 Weeks)
    const toggle7d = document.getElementById("toggle7dBtn");
    const toggle6w = document.getElementById("toggle6wBtn");
    const chartView7d = document.getElementById("chartView7d");
    const chartView6w = document.getElementById("chartView6w");

    if (toggle7d && toggle6w && chartView7d && chartView6w) {
      toggle7d.addEventListener("click", function () {
        toggle7d.classList.add("active");
        toggle7d.setAttribute("aria-selected", "true");
        toggle6w.classList.remove("active");
        toggle6w.setAttribute("aria-selected", "false");
        chartView7d.style.display = "block";
        chartView6w.style.display = "none";
      });

      toggle6w.addEventListener("click", function () {
        toggle6w.classList.add("active");
        toggle6w.setAttribute("aria-selected", "true");
        toggle7d.classList.remove("active");
        toggle7d.setAttribute("aria-selected", "false");
        chartView7d.style.display = "none";
        chartView6w.style.display = "block";
      });
    }

    // 17g. Live Assignment Deadlines Countdown Helper
    function formatCountdown(rawDeadline) {
      if (!rawDeadline) return { text: "Open Term", urgent: false, passed: false };
      const deadlineDate = new Date(rawDeadline.replace(" ", "T")).getTime();
      const now = new Date().getTime();
      const diff = deadlineDate - now;

      if (isNaN(deadlineDate)) return { text: "Open Term", urgent: false, passed: false };
      if (diff <= 0) return { text: "Deadline Passed", urgent: false, passed: true };

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const isUrgent = diff < 24 * 60 * 60 * 1000;

      if (days > 0) {
        return { text: `${days}d ${hours}h left`, urgent: isUrgent, passed: false };
      } else {
        return { text: `${hours}h ${minutes}m left`, urgent: isUrgent, passed: false };
      }
    }

    function updateCountdowns() {
      // Assignment cards
      document.querySelectorAll(".deadline-countdown-badge").forEach(badge => {
        const raw = badge.getAttribute("data-deadline");
        const textSpan = badge.querySelector(".countdown-text") || badge;
        const res = formatCountdown(raw);
        textSpan.textContent = res.text;
        if (res.urgent) badge.classList.add("deadline-urgent");
        else badge.classList.remove("deadline-urgent");
      });

      // Hero deadline strip
      document.querySelectorAll(".deadline-strip-timer").forEach(timer => {
        const raw = timer.getAttribute("data-deadline");
        const res = formatCountdown(raw);
        timer.textContent = res.text;
        if (res.urgent) timer.classList.add("deadline-urgent");
        else timer.classList.remove("deadline-urgent");
      });

      // Timeline timers
      document.querySelectorAll(".timeline-timer").forEach(timer => {
        const raw = timer.getAttribute("data-deadline");
        const res = formatCountdown(raw);
        timer.textContent = res.text;
        if (res.urgent) timer.classList.add("urgent");
        else timer.classList.remove("urgent");
      });
    }
    updateCountdowns();
    setInterval(updateCountdowns, 60000);

    // 17h. Quick Submit Dropzone
    const quickDropzone = document.getElementById("quickDropzoneArea");
    const quickFileInput = document.getElementById("quickFileInput");
    if (quickDropzone && quickFileInput) {
      function handleQuickFile(file) {
        if (!file) return;
        const reader = new FileReader();
        reader.onload = function (e) {
          try {
            sessionStorage.setItem("codeguard_quick_file", JSON.stringify({
              name: file.name,
              content: e.target.result
            }));
          } catch (err) {}
          window.location.href = "/student/submit";
        };
        reader.readAsText(file);
      }

      ["dragenter", "dragover"].forEach(eventName => {
        quickDropzone.addEventListener(eventName, function (e) {
          e.preventDefault();
          e.stopPropagation();
          quickDropzone.classList.add("drag-over");
        });
      });

      ["dragleave", "drop"].forEach(eventName => {
        quickDropzone.addEventListener(eventName, function (e) {
          e.preventDefault();
          e.stopPropagation();
          quickDropzone.classList.remove("drag-over");
        });
      });

      quickDropzone.addEventListener("drop", function (e) {
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          handleQuickFile(e.dataTransfer.files[0]);
        }
      });

      quickFileInput.addEventListener("change", function () {
        if (this.files && this.files.length > 0) {
          handleQuickFile(this.files[0]);
        }
      });

      quickDropzone.addEventListener("click", function (e) {
        if (e.target !== quickFileInput) {
          quickFileInput.click();
        }
      });
    }

    // 17i. Live In-Page Filtering with Topbar Search
    const searchInput = document.getElementById("globalSearchInput");
    if (searchInput) {
      searchInput.addEventListener("input", function () {
        const query = this.value.trim().toLowerCase();
        
        // Filter Assignment tiles
        document.querySelectorAll(".assignment-tile").forEach(tile => {
          const title = tile.getAttribute("data-asgn-title") || "";
          const subj = tile.getAttribute("data-asgn-subj") || "";
          if (!query || title.includes(query) || subj.includes(query)) {
            tile.style.display = "flex";
          } else {
            tile.style.display = "none";
          }
        });

        // Filter Recent Submissions rows
        document.querySelectorAll(".submission-row").forEach(row => {
          const text = row.getAttribute("data-search-text") || "";
          if (!query || text.includes(query)) {
            row.style.display = "";
          } else {
            row.style.display = "none";
          }
        });
      });

      searchInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && this.value.trim() !== "") {
          window.location.href = `/student/submissions?q=${encodeURIComponent(this.value.trim())}`;
        }
      });
    }

    // 17j. Pending Screening Auto-Refresh (every 10s if pending submissions exist)
    const pendingCount = parseInt(studentDashboard.getAttribute("data-pending"), 10) || 0;
    if (pendingCount > 0) {
      let secondsLeft = 10;
      const countdownSpan = document.getElementById("queueCountdown");
      const pollTimer = setInterval(() => {
        secondsLeft -= 1;
        if (countdownSpan) countdownSpan.textContent = secondsLeft;
        if (secondsLeft <= 0) {
          clearInterval(pollTimer);
          window.location.reload();
        }
      }, 1000);
    }
  }

  // 18. Quick Submit Pre-fill listener on /student/submit page
  try {
    const quickFileRaw = sessionStorage.getItem("codeguard_quick_file");
    if (quickFileRaw) {
      const quickFile = JSON.parse(quickFileRaw);
      sessionStorage.removeItem("codeguard_quick_file");
      const pasteTabBtn = document.querySelector('[data-tab-target="tabPasteCode"]');
      const codeTextArea = document.getElementById("code_text");
      const titleInput = document.getElementById("title");
      if (pasteTabBtn && codeTextArea) {
        pasteTabBtn.click();
        codeTextArea.value = quickFile.content;
        codeTextArea.dispatchEvent(new Event("input", { bubbles: true }));
        if (titleInput && !titleInput.value) {
          titleInput.value = quickFile.name;
        }
      }
    }
  } catch (e) {}
});

