// CodeGuard Course Assignments Management Controller
document.addEventListener("DOMContentLoaded", function () {
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


