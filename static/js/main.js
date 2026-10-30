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

  // ─────────────────────────────────────────────────────────────────────────
  // 22. Manage Course Assignments Controller
  // ─────────────────────────────────────────────────────────────────────────
  const asgnApp = document.getElementById("assignmentsManagementApp");
  if (asgnApp) {
    initAssignmentsController();
  }

  function initAssignmentsController() {
    // DOM Elements
    const searchInput = document.getElementById("asgnSearchInput");
    const searchClearBtn = document.getElementById("asgnSearchClearBtn");
    const statusFilter = document.getElementById("asgnStatusFilter");
    const langFilter = document.getElementById("asgnLangFilter");
    const sortSelect = document.getElementById("asgnSortSelect");
    const tableBody = document.getElementById("asgnTableBody");
    const showingCount = document.getElementById("asgnShowingCount");
    const totalCount = document.getElementById("asgnTotalCount");
    const emptyState = document.getElementById("asgnEmptyState");
    const btnResetFilters = document.getElementById("btnResetFilters");
    const btnRefreshTable = document.getElementById("btnRefreshTable");
    const btnOpenNewAsgn = document.getElementById("btnOpenNewAssignmentModal");
    const btnEmptyCreate = document.getElementById("btnEmptyCreateAssignment");
    const formPanel = document.getElementById("asgnFormPanel");
    const formCard = document.getElementById("asgnFormCard");
    const btnDrawerClose = document.getElementById("btnDrawerClose");
    const drawerBackdrop = document.getElementById("asgnDrawerBackdrop");
    const createForm = document.getElementById("createAssignmentForm");
    const formModeTitle = document.getElementById("formModeTitle");
    const editAssignmentId = document.getElementById("editAssignmentId");
    const asgnTitle = document.getElementById("asgnTitle");
    const asgnSubject = document.getElementById("asgnSubject");
    const asgnDesc = document.getElementById("asgnDescription");
    const asgnDeadline = document.getElementById("asgnDeadline");
    const btnSubmitAssignment = document.getElementById("btnSubmitAssignment");
    const btnSubmitLabel = document.getElementById("btnSubmitLabel");
    const btnSubmitSpinner = document.getElementById("btnSubmitSpinner");
    const btnSaveDraft = document.getElementById("btnSaveDraft");
    const btnResetForm = document.getElementById("btnResetForm");
    const confirmModal = document.getElementById("asgnConfirmModal");
    const btnModalCancel = document.getElementById("btnModalCancel");
    const modalConfirmForm = document.getElementById("modalConfirmForm");
    const modalTargetAsgn = document.getElementById("modalTargetAsgn");
    const modalConsequenceText = document.getElementById("modalConsequenceText");
    const toast = document.getElementById("asgnToast");
    const toastTitle = document.getElementById("toastTitle");
    const toastMessage = document.getElementById("toastMessage");
    const toastUndoBtn = document.getElementById("toastUndoBtn");
    const toastCloseBtn = document.getElementById("toastCloseBtn");
    const timezoneBadge = document.getElementById("clientTimezoneBadge");
    const thSortDeadline = document.getElementById("thSortDeadline");
    const thSortSubmissions = document.getElementById("thSortSubmissions");

    let toastTimer = null;
    let lastUndoAction = null;

    // Detect Client Timezone
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "Local";
      if (timezoneBadge) {
        timezoneBadge.textContent = "Timezone: " + tz;
      }
    } catch (_) {}

    // Format Deadlines and compute relative hints
    const now = new Date();
    document.querySelectorAll(".deadline-formatted").forEach(el => {
      const raw = el.getAttribute("data-timestamp");
      if (!raw) return;

      // Parse SQL timestamp "YYYY-MM-DD HH:MM:SS" or ISO
      const d = parseDateTime(raw);
      if (!d || isNaN(d.getTime())) return;

      // Nice formatted string: e.g. "30 Nov 2026, 11:59 PM"
      const options = { day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit" };
      el.textContent = d.toLocaleDateString(undefined, options);

      // Relative hint underneath
      const hint = el.parentElement.querySelector(".deadline-relative-hint");
      if (!hint) return;

      const diffMs = d.getTime() - now.getTime();
      const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
      const diffHours = Math.ceil(diffMs / (1000 * 60 * 60));

      if (diffMs < 0) {
        hint.textContent = "Overdue (Past deadline)";
        hint.classList.add("overdue");
        // Tag row as past
        const row = el.closest(".assignment-row");
        if (row) {
          row.setAttribute("data-is-past", "1");
          const pill = row.querySelector(".status-indicator-pill");
          if (pill && pill.classList.contains("status-active")) {
            pill.className = "status-indicator-pill status-closed";
            pill.innerHTML = '<span class="status-static-dot"></span><span>Closed</span>';
          }
        }
      } else if (diffHours <= 72) {
        hint.textContent = diffHours <= 24 ? `Due in ${diffHours} hr${diffHours === 1 ? '' : 's'}` : `Due in ${diffDays} days`;
        hint.classList.add("urgent");
      } else {
        hint.textContent = `in ${diffDays} days`;
      }
    });

    function parseDateTime(str) {
      if (!str) return null;
      // Replace space with T if needed: "2026-11-30 23:59:00" -> "2026-11-30T23:59:00"
      const s = str.trim().replace(" ", "T");
      return new Date(s);
    }

    // Set min deadline on date picker to now
    if (asgnDeadline) {
      const isoNow = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
      asgnDeadline.min = isoNow;
    }

    // Deadline Presets
    document.querySelectorAll(".preset-chip-btn").forEach(btn => {
      btn.addEventListener("click", function () {
        const targetDate = new Date();
        const days = parseInt(this.getAttribute("data-days"), 10);
        const preset = this.getAttribute("data-preset");

        if (preset === "eom") {
          // Last day of current month
          targetDate.setMonth(targetDate.getMonth() + 1, 0);
        } else if (!isNaN(days)) {
          targetDate.setDate(targetDate.getDate() + days);
        }

        // Set cutoff time to 23:59:00
        targetDate.setHours(23, 59, 0, 0);

        if (asgnDeadline) {
          const pad = n => String(n).padStart(2, "0");
          const formatted = `${targetDate.getFullYear()}-${pad(targetDate.getMonth() + 1)}-${pad(targetDate.getDate())}T23:59`;
          asgnDeadline.value = formatted;
          asgnDeadline.dispatchEvent(new Event("change"));
        }
      });
    });

    // Expandable descriptions
    document.querySelectorAll(".desc-expand-pill").forEach(btn => {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        const targetId = this.getAttribute("data-target");
        const p = document.getElementById(targetId);
        if (p) {
          const isExpanded = p.classList.toggle("expanded");
          this.textContent = isExpanded ? "Collapse" : "Expand";
          p.setAttribute("aria-expanded", String(isExpanded));
        }
      });
    });

    document.querySelectorAll(".assignment-desc-truncated").forEach(p => {
      p.addEventListener("click", function () {
        const isExpanded = this.classList.toggle("expanded");
        const btn = this.parentElement.querySelector(".desc-expand-pill");
        if (btn) btn.textContent = isExpanded ? "Collapse" : "Expand";
        this.setAttribute("aria-expanded", String(isExpanded));
      });
    });

    // Language Chips Grid in Form
    const langBoxes = document.querySelectorAll(".lang-hidden-input");
    const langError = document.getElementById("langError");

    document.querySelectorAll(".lang-toggle-box").forEach(box => {
      const chk = box.querySelector(".lang-hidden-input");
      if (chk) {
        chk.addEventListener("change", function () {
          if (langError) langError.style.display = "none";
        });
      }
    });

    const btnSelectAllLangs = document.getElementById("btnSelectAllLangs");
    const btnClearLangs = document.getElementById("btnClearLangs");

    if (btnSelectAllLangs) {
      btnSelectAllLangs.addEventListener("click", function () {
        langBoxes.forEach(b => { b.checked = true; });
        if (langError) langError.style.display = "none";
      });
    }

    if (btnClearLangs) {
      btnClearLangs.addEventListener("click", function () {
        langBoxes.forEach(b => { b.checked = false; });
      });
    }

    // Character Counters
    setupCharCounter(asgnTitle, document.getElementById("titleCharCounter"), 100);
    setupCharCounter(asgnSubject, document.getElementById("subjectCharCounter"), 80);
    setupCharCounter(asgnDesc, document.getElementById("descCharCounter"), 1000);

    function setupCharCounter(input, counterEl, max) {
      if (!input || !counterEl) return;
      const update = () => {
        const len = (input.value || "").length;
        counterEl.textContent = `${len} / ${max}`;
        if (len >= max) {
          counterEl.style.color = "#ef4444";
        } else {
          counterEl.style.color = "var(--text-muted)";
        }
      };
      input.addEventListener("input", update);
      update();
    }

    // Auto-growing textarea
    if (asgnDesc) {
      asgnDesc.addEventListener("input", function () {
        this.style.height = "auto";
        this.style.height = Math.min(this.scrollHeight, 260) + "px";
      });
    }

    // Markdown Write / Preview Tabs
    const tabWrite = document.getElementById("tabDescWrite");
    const tabPreview = document.getElementById("tabDescPreview");
    const descPreviewPane = document.getElementById("descMarkdownPreview");

    if (tabWrite && tabPreview && descPreviewPane && asgnDesc) {
      tabWrite.addEventListener("click", function () {
        tabWrite.classList.add("active");
        tabPreview.classList.remove("active");
        tabWrite.setAttribute("aria-selected", "true");
        tabPreview.setAttribute("aria-selected", "false");
        asgnDesc.style.display = "block";
        descPreviewPane.style.display = "none";
      });

      tabPreview.addEventListener("click", function () {
        tabPreview.classList.add("active");
        tabWrite.classList.remove("active");
        tabPreview.setAttribute("aria-selected", "true");
        tabWrite.setAttribute("aria-selected", "false");
        asgnDesc.style.display = "none";
        descPreviewPane.style.display = "block";

        const text = (asgnDesc.value || "").trim();
        if (!text) {
          descPreviewPane.innerHTML = '<em style="color: var(--text-muted); font-size: 0.82rem;">Nothing to preview yet. Enter text in Write tab.</em>';
        } else {
          // Simple safe markdown render
          let html = text
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/`([^`]+)`/g, "<code>$1</code>")
            .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
            .replace(/\*([^*]+)\*/g, "<em>$1</em>")
            .replace(/^\s*[-*]\s+(.*)$/gim, "<li>$1</li>")
            .replace(/\n/g, "<br>");
          descPreviewPane.innerHTML = html;
        }
      });
    }

    // Collapsible Advanced Settings
    const btnToggleAdvanced = document.getElementById("btnToggleAdvanced");
    const advancedBody = document.getElementById("advancedSettingsBody");
    if (btnToggleAdvanced && advancedBody) {
      btnToggleAdvanced.addEventListener("click", function () {
        const isExp = this.getAttribute("aria-expanded") === "true";
        this.setAttribute("aria-expanded", String(!isExp));
        advancedBody.style.display = isExp ? "none" : "block";
      });
    }

    // Plagiarism Threshold Override slider
    const threshInput = document.getElementById("similarityThresholdInput");
    const threshDisplay = document.getElementById("thresholdDisplay");
    if (threshInput && threshDisplay) {
      threshInput.addEventListener("input", function () {
        threshDisplay.textContent = this.value + "%";
      });
    }

    // Drawer Open / Close for Screens <= 1100px
    function openDrawer() {
      if (!formPanel) return;
      if (window.innerWidth <= 1100) {
        formPanel.classList.add("drawer-open");
        document.body.classList.add("drawer-active");
        if (asgnTitle) asgnTitle.focus();
      } else {
        // Desktop: smoothly scroll to form and pulse outline
        formCard.scrollIntoView({ behavior: "smooth", block: "start" });
        formCard.classList.add("highlight-focus");
        setTimeout(() => { formCard.classList.remove("highlight-focus"); }, 1500);
        if (asgnTitle) asgnTitle.focus();
      }
    }

    function closeDrawer() {
      if (formPanel) {
        formPanel.classList.remove("drawer-open");
        document.body.classList.remove("drawer-active");
      }
    }

    if (btnOpenNewAsgn) btnOpenNewAsgn.addEventListener("click", openDrawer);
    if (btnEmptyCreate) btnEmptyCreate.addEventListener("click", openDrawer);
    if (btnDrawerClose) btnDrawerClose.addEventListener("click", closeDrawer);
    if (drawerBackdrop) drawerBackdrop.addEventListener("click", closeDrawer);

    // Filter & Search Implementation
    const rows = Array.from(document.querySelectorAll(".assignment-row"));
    if (totalCount) totalCount.textContent = rows.length;

    function applyFilters() {
      const q = (searchInput ? searchInput.value : "").trim().toLowerCase();
      const status = statusFilter ? statusFilter.value : "all";
      const lang = langFilter ? langFilter.value : "all";

      let matchedCount = 0;

      rows.forEach(row => {
        const title = (row.getAttribute("data-title") || "").toLowerCase();
        const subject = (row.getAttribute("data-subject") || "").toLowerCase();
        const id = (row.getAttribute("data-id") || "").toLowerCase();
        const languages = (row.getAttribute("data-languages") || "").toLowerCase();
        const isActive = row.getAttribute("data-active") === "1";
        const isPast = row.getAttribute("data-is-past") === "1";

        // Query match
        const matchesQuery = !q || title.includes(q) || subject.includes(q) || id.includes(q);

        // Status match
        let matchesStatus = true;
        if (status === "active") matchesStatus = isActive && !isPast;
        else if (status === "disabled") matchesStatus = !isActive;
        else if (status === "past") matchesStatus = isPast;

        // Language match
        let matchesLang = true;
        if (lang !== "all") {
          matchesLang = languages.split(",").map(s => s.trim()).includes(lang);
        }

        if (matchesQuery && matchesStatus && matchesLang) {
          row.style.display = "";
          matchedCount++;
        } else {
          row.style.display = "none";
        }
      });

      if (showingCount) showingCount.textContent = matchedCount;
      if (searchClearBtn) searchClearBtn.style.display = q ? "block" : "none";

      // Show/Hide Empty State
      if (emptyState) {
        if (matchedCount === 0) {
          emptyState.style.display = "block";
          if (btnResetFilters) {
            btnResetFilters.style.display = (q || status !== "all" || lang !== "all") ? "inline-block" : "none";
          }
        } else {
          emptyState.style.display = "none";
        }
      }
    }

    if (searchInput) searchInput.addEventListener("input", applyFilters);
    if (statusFilter) statusFilter.addEventListener("change", applyFilters);
    if (langFilter) langFilter.addEventListener("change", applyFilters);

    if (searchClearBtn) {
      searchClearBtn.addEventListener("click", function () {
        if (searchInput) {
          searchInput.value = "";
          searchInput.focus();
          applyFilters();
        }
      });
    }

    if (btnResetFilters) {
      btnResetFilters.addEventListener("click", function () {
        if (searchInput) searchInput.value = "";
        if (statusFilter) statusFilter.value = "all";
        if (langFilter) langFilter.value = "all";
        applyFilters();
      });
    }

    if (btnRefreshTable) {
      btnRefreshTable.addEventListener("click", function () {
        const skeleton = document.getElementById("asgnSkeletonLoader");
        if (skeleton) skeleton.style.display = "block";
        tableBody.style.opacity = "0.3";
        setTimeout(() => {
          if (skeleton) skeleton.style.display = "none";
          tableBody.style.opacity = "1";
          applyFilters();
          showToast("Assignments table refreshed.", "Updated");
        }, 350);
      });
    }

    // Sorting
    function sortTable(key, order) {
      const sorted = [...rows].sort((a, b) => {
        let valA, valB;
        if (key === "deadline") {
          valA = a.getAttribute("data-deadline") || "9999-99-99";
          valB = b.getAttribute("data-deadline") || "9999-99-99";
        } else if (key === "submissions") {
          valA = parseInt(a.getAttribute("data-submissions") || "0", 10);
          valB = parseInt(b.getAttribute("data-submissions") || "0", 10);
        } else if (key === "newest") {
          valA = parseInt(a.getAttribute("data-id") || "0", 10);
          valB = parseInt(b.getAttribute("data-id") || "0", 10);
          return valB - valA;
        } else if (key === "title") {
          valA = (a.getAttribute("data-title") || "").toLowerCase();
          valB = (b.getAttribute("data-title") || "").toLowerCase();
        }

        if (valA < valB) return order === "asc" ? -1 : 1;
        if (valA > valB) return order === "asc" ? 1 : -1;
        return 0;
      });

      sorted.forEach(row => tableBody.appendChild(row));
    }

    if (sortSelect) {
      sortSelect.addEventListener("change", function () {
        const val = this.value;
        if (val === "deadline_asc") sortTable("deadline", "asc");
        else if (val === "deadline_desc") sortTable("deadline", "desc");
        else if (val === "submissions_desc") sortTable("submissions", "desc");
        else if (val === "newest") sortTable("newest", "desc");
        else if (val === "title_asc") sortTable("title", "asc");
      });
    }

    // Clickable table header sorting
    let deadlineSortAsc = true;
    if (thSortDeadline) {
      thSortDeadline.addEventListener("click", function () {
        deadlineSortAsc = !deadlineSortAsc;
        thSortDeadline.className = deadlineSortAsc ? "th-deadline sortable-th active-asc" : "th-deadline sortable-th active-desc";
        sortTable("deadline", deadlineSortAsc ? "asc" : "desc");
      });
    }

    let subSortAsc = false;
    if (thSortSubmissions) {
      thSortSubmissions.addEventListener("click", function () {
        subSortAsc = !subSortAsc;
        thSortSubmissions.className = subSortAsc ? "th-submissions sortable-th active-asc" : "th-submissions sortable-th active-desc";
        sortTable("submissions", subSortAsc ? "asc" : "desc");
      });
    }

    // Overflow Dropdown Menus (⋯)
    document.querySelectorAll(".btn-overflow-trigger").forEach(btn => {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        const menuId = this.id.replace("btnOverflow-", "menu-");
        const targetMenu = document.getElementById(menuId);
        const isOpen = targetMenu && targetMenu.classList.contains("active");

        // Close all menus
        closeAllOverflowMenus();

        if (!isOpen && targetMenu) {
          targetMenu.classList.add("active");
          this.setAttribute("aria-expanded", "true");
        }
      });
    });

    function closeAllOverflowMenus() {
      document.querySelectorAll(".overflow-dropdown-menu.active").forEach(m => m.classList.remove("active"));
      document.querySelectorAll(".btn-overflow-trigger[aria-expanded='true']").forEach(b => b.setAttribute("aria-expanded", "false"));
    }

    document.addEventListener("click", closeAllOverflowMenus);

    // Edit Assignment Action
    document.querySelectorAll(".btn-action-edit").forEach(btn => {
      btn.addEventListener("click", function () {
        const asgnId = this.getAttribute("data-asgn-id");
        const row = document.getElementById("asgn-row-" + asgnId);
        if (!row) return;

        const title = row.getAttribute("data-title") || "";
        const subject = row.getAttribute("data-subject") || "";
        const desc = row.getAttribute("data-description") || "";
        const langs = (row.getAttribute("data-languages") || "").split(",").map(s => s.trim().toLowerCase());
        const deadline = row.getAttribute("data-deadline") || "";

        if (asgnTitle) asgnTitle.value = title;
        if (asgnSubject) asgnSubject.value = subject;
        if (asgnDesc) {
          asgnDesc.value = desc;
          asgnDesc.dispatchEvent(new Event("input"));
        }
        if (asgnDeadline && deadline) {
          asgnDeadline.value = deadline.replace(" ", "T").slice(0, 16);
        }
        if (editAssignmentId) editAssignmentId.value = asgnId;

        // Check language boxes
        langBoxes.forEach(box => {
          box.checked = langs.includes(box.value.toLowerCase());
        });

        if (formModeTitle) formModeTitle.textContent = "Edit Assignment #" + asgnId;
        if (btnSubmitLabel) btnSubmitLabel.textContent = "Save Changes";

        openDrawer();
      });
    });

    // Duplicate Template Action
    document.querySelectorAll(".item-duplicate-asgn").forEach(btn => {
      btn.addEventListener("click", function () {
        closeAllOverflowMenus();
        const title = this.getAttribute("data-asgn-title");
        const subject = this.getAttribute("data-asgn-subject");
        const desc = this.getAttribute("data-asgn-desc");
        const langs = (this.getAttribute("data-asgn-langs") || "").split(",").map(s => s.trim().toLowerCase());

        if (asgnTitle) asgnTitle.value = title + " (Copy)";
        if (asgnSubject) asgnSubject.value = subject;
        if (asgnDesc) {
          asgnDesc.value = desc;
          asgnDesc.dispatchEvent(new Event("input"));
        }
        if (editAssignmentId) editAssignmentId.value = "";

        langBoxes.forEach(box => {
          box.checked = langs.includes(box.value.toLowerCase());
        });

        if (formModeTitle) formModeTitle.textContent = "+ Create Assignment";
        if (btnSubmitLabel) btnSubmitLabel.textContent = "Create Assignment";

        openDrawer();
        showToast("Template pre-filled from " + title, "Duplicate Ready");
      });
    });

    // Toggle Disable / Enable with Consequences Modal
    document.querySelectorAll(".item-toggle-status").forEach(btn => {
      btn.addEventListener("click", function () {
        closeAllOverflowMenus();
        const asgnId = this.getAttribute("data-asgn-id");
        const title = this.getAttribute("data-asgn-title");
        const isActive = this.getAttribute("data-is-active") === "1";
        const toggleUrl = this.getAttribute("data-toggle-url");

        if (modalTargetAsgn) modalTargetAsgn.textContent = `#${asgnId}: ${title}`;
        if (modalConfirmForm) modalConfirmForm.action = toggleUrl;

        const modalTitle = document.getElementById("modalDialogTitle");
        const modalDesc = document.getElementById("modalDialogDesc");
        const btnModalConfirm = document.getElementById("btnModalConfirm");

        if (isActive) {
          if (modalTitle) modalTitle.textContent = "Disable Assignment?";
          if (modalDesc) modalDesc.textContent = `Are you sure you want to disable '${title}'?`;
          if (modalConsequenceText) {
            modalConsequenceText.textContent = "Students will no longer be able to submit solutions to this assignment. Existing submissions and plagiarism scores are safely preserved.";
          }
          if (btnModalConfirm) {
            btnModalConfirm.textContent = "Disable Assignment";
            btnModalConfirm.className = "btn btn-sm btn-danger";
          }
        } else {
          if (modalTitle) modalTitle.textContent = "Enable Assignment?";
          if (modalDesc) modalDesc.textContent = `Are you sure you want to reactivate '${title}'?`;
          if (modalConsequenceText) {
            modalConsequenceText.textContent = "Students will immediately be allowed to submit code solutions up to the configured deadline.";
          }
          if (btnModalConfirm) {
            btnModalConfirm.textContent = "Enable Assignment";
            btnModalConfirm.className = "btn btn-sm btn-primary";
          }
        }

        if (confirmModal) {
          if (typeof confirmModal.showModal === "function") {
            confirmModal.showModal();
          } else {
            if (confirm(`Confirm ${isActive ? "disabling" : "enabling"} '${title}'?`)) {
              modalConfirmForm.submit();
            }
          }
        }
      });
    });

    // Delete Assignment with Consequences Dialog
    document.querySelectorAll(".item-delete-asgn").forEach(btn => {
      btn.addEventListener("click", function () {
        closeAllOverflowMenus();
        const asgnId = this.getAttribute("data-asgn-id");
        const title = this.getAttribute("data-asgn-title");

        if (modalTargetAsgn) modalTargetAsgn.textContent = `#${asgnId}: ${title}`;
        const modalTitle = document.getElementById("modalDialogTitle");
        const modalDesc = document.getElementById("modalDialogDesc");
        const btnModalConfirm = document.getElementById("btnModalConfirm");

        if (modalTitle) modalTitle.textContent = "Delete Assignment Record";
        if (modalDesc) modalDesc.textContent = `Permanently delete assignment #${asgnId} ('${title}')?`;
        if (modalConsequenceText) {
          modalConsequenceText.textContent = "This action removes the assignment from active student listings. Student submissions linked to this assignment will be archived.";
        }
        if (btnModalConfirm) {
          btnModalConfirm.textContent = "Delete Assignment";
          btnModalConfirm.className = "btn btn-sm btn-danger";
        }

        if (confirmModal) {
          if (typeof confirmModal.showModal === "function") {
            confirmModal.showModal();
          } else {
            alert("Delete action requested for " + title);
          }
        }
      });
    });

    if (btnModalCancel && confirmModal) {
      btnModalCancel.addEventListener("click", function () {
        confirmModal.close();
      });
    }

    // Reset Form button
    if (btnResetForm) {
      btnResetForm.addEventListener("click", function () {
        if (editAssignmentId) editAssignmentId.value = "";
        if (formModeTitle) formModeTitle.textContent = "+ Create Assignment";
        if (btnSubmitLabel) btnSubmitLabel.textContent = "Create Assignment";
        langBoxes.forEach(b => { b.checked = false; });
        document.querySelectorAll(".form-error-msg").forEach(el => { el.style.display = "none"; });
        if (asgnDesc) asgnDesc.dispatchEvent(new Event("input"));
      });
    }

    // Save as Draft action (Simulated / TODO)
    if (btnSaveDraft) {
      btnSaveDraft.addEventListener("click", function () {
        // // TODO: connect API for draft save action
        const title = (asgnTitle ? asgnTitle.value : "").trim() || "Untitled Assignment";
        showToast(`Draft for '${title}' saved locally.`, "Draft Saved");
        closeDrawer();
      });
    }

    // Form Inline Validation & Submission
    if (createForm) {
      createForm.addEventListener("submit", function (e) {
        let isValid = true;

        // Title validation
        const titleVal = (asgnTitle ? asgnTitle.value : "").trim();
        const titleErr = document.getElementById("titleError");
        if (!titleVal) {
          if (titleErr) {
            titleErr.textContent = "Assignment title is required.";
            titleErr.style.display = "block";
          }
          isValid = false;
        } else if (titleErr) {
          titleErr.style.display = "none";
        }

        // Subject validation
        const subjectVal = (asgnSubject ? asgnSubject.value : "").trim();
        const subjectErr = document.getElementById("subjectError");
        if (!subjectVal) {
          if (subjectErr) {
            subjectErr.textContent = "Course subject category is required.";
            subjectErr.style.display = "block";
          }
          isValid = false;
        } else if (subjectErr) {
          subjectErr.style.display = "none";
        }

        // Permitted languages validation
        const checkedLangs = Array.from(langBoxes).filter(b => b.checked);
        if (checkedLangs.length === 0) {
          if (langError) {
            langError.textContent = "Select at least one permitted programming language parser.";
            langError.style.display = "block";
          }
          isValid = false;
        } else if (langError) {
          langError.style.display = "none";
        }

        if (!isValid) {
          e.preventDefault();
          return false;
        }

        // Show spinner and disable button
        if (btnSubmitSpinner) btnSubmitSpinner.style.display = "inline-block";
        if (btnSubmitAssignment) {
          btnSubmitAssignment.disabled = true;
          if (btnSubmitLabel) btnSubmitLabel.textContent = "Processing...";
        }
      });
    }

    // Toast Notification System with Undo
    function showToast(message, title = "Notification", undoCallback = null) {
      if (!toast) return;
      if (toastTitle) toastTitle.textContent = title;
      if (toastMessage) toastMessage.textContent = message;

      if (undoCallback && toastUndoBtn) {
        toastUndoBtn.style.display = "inline-block";
        lastUndoAction = undoCallback;
      } else if (toastUndoBtn) {
        toastUndoBtn.style.display = "none";
      }

      toast.style.display = "flex";

      if (toastTimer) clearTimeout(toastTimer);
      toastTimer = setTimeout(dismissToast, 4500);
    }

    function dismissToast() {
      if (toast) toast.style.display = "none";
      if (toastTimer) clearTimeout(toastTimer);
      lastUndoAction = null;
    }

    if (toastCloseBtn) toastCloseBtn.addEventListener("click", dismissToast);

    if (toastUndoBtn) {
      toastUndoBtn.addEventListener("click", function () {
        if (typeof lastUndoAction === "function") {
          lastUndoAction();
          showToast("Action reverted.", "Undone");
        }
        dismissToast();
      });
    }

    // Keyboard support: Esc closes modals & drawers
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" || e.key === "Esc") {
        closeAllOverflowMenus();
        closeDrawer();
        if (confirmModal && confirmModal.open) confirmModal.close();
        if (logoutModal && logoutModal.open) logoutModal.close();
      }
    });
  }

});

