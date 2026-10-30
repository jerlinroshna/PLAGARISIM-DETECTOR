// CodeGuard Student Dashboard & Workspace Module
document.addEventListener("DOMContentLoaded", function () {
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
