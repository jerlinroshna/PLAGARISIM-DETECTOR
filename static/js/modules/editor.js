// CodeGuard Code Editor, Upload & Submission Validation Module
document.addEventListener("DOMContentLoaded", function () {
  // 3. Multi-Language Syntax Auto-Detector
  function detectLanguageFromCode(code) {
    if (!code || !code.trim()) return null;
    const s = code.trim();

    // C++ indicators
    if (/#include\s*<iostream>|std::|cout\s*<<|cin\s*>>|namespace\s+std|#include\s*<vector>|#include\s*<string>/i.test(s)) {
      return "cpp";
    }
    // C indicators
    if (/#include\s*<stdio\.h>|#include\s*<stdlib\.h>|#include\s*<string\.h>|printf\s*\(|scanf\s*\(|int\s+main\s*\(/i.test(s)) {
      return "c";
    }
    // Java indicators
    if (/public\s+class\s+|System\.out\.(println|print)|public\s+static\s+void\s+main/i.test(s)) {
      return "java";
    }
    // Python indicators
    if (/def\s+[a-zA-Z0-9_]+\s*\(|import\s+[a-zA-Z0-9_]+|from\s+[a-zA-Z0-9_]+\s+import|if\s+__name__\s*==|elif\s+|print\s*\(/i.test(s)) {
      return "python";
    }
    // JavaScript indicators
    if (/console\.log\s*\(|function\s+[a-zA-Z0-9_]+\s*\(|const\s+[a-zA-Z0-9_]+\s*=|let\s+[a-zA-Z0-9_]+\s*=|document\.getElementById/i.test(s)) {
      return "javascript";
    }
    return null;
  }

  // 4. Tab switching (Upload File vs Paste Code) & Mode Tracking
  const tabButtons = document.querySelectorAll(".portal-tab-btn");
  const submissionModeInput = document.getElementById("submission_mode");
  const dropzone = document.getElementById("uploadDropzone");
  const fileInput = document.getElementById("code_file");
  const filePreview = document.getElementById("filePreviewInfo");
  const langSelect = document.getElementById("programming_language");
  const codeTextarea = document.getElementById("code_text");
  const detectedLangBadge = document.getElementById("detectedLangBadge");
  const chkLangName = document.getElementById("chk-lang-name");

  function handlePastedCodeAnalysis() {
    if (!codeTextarea) return;
    const text = codeTextarea.value;
    const detected = detectLanguageFromCode(text);

    if (detected && langSelect) {
      if (langSelect.value === "auto" || langSelect.getAttribute("data-user-selected") !== "true") {
        langSelect.value = detected;
      }
      if (detectedLangBadge) {
        detectedLangBadge.textContent = "Detected: " + detected.toUpperCase();
        detectedLangBadge.style.display = "inline-block";
      }
    } else if (detectedLangBadge) {
      if (langSelect && langSelect.value !== "auto") {
        detectedLangBadge.textContent = "Language: " + langSelect.value.toUpperCase();
        detectedLangBadge.style.display = "inline-block";
      } else {
        detectedLangBadge.style.display = "none";
      }
    }
  }

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

      if (targetId === "tabPasteCode") {
        if (submissionModeInput) submissionModeInput.value = "paste";
        if (fileInput) fileInput.value = "";
        if (filePreview) filePreview.style.display = "none";
        if (codeTextarea) {
          codeTextarea.focus();
          handlePastedCodeAnalysis();
        }
      } else {
        if (submissionModeInput) submissionModeInput.value = "upload";
      }
      updateChecklist();
    });
  });

  // Quick Language Select Buttons
  document.querySelectorAll(".btn-lang-quick").forEach(btn => {
    btn.addEventListener("click", function () {
      const l = this.getAttribute("data-lang");
      if (l && langSelect) {
        langSelect.value = l;
        langSelect.setAttribute("data-user-selected", "true");
        if (detectedLangBadge) {
          detectedLangBadge.textContent = "Language: " + l.toUpperCase();
          detectedLangBadge.style.display = "inline-block";
        }
        updateChecklist();
      }
    });
  });

  // 5. File Drag & Drop and Preview
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

    if (submissionModeInput) submissionModeInput.value = "upload";
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

  // 6. Code editor statistics and Tab key handling
  const statLines = document.getElementById("stat-lines");
  const statChars = document.getElementById("stat-chars");
  const statFuncs = document.getElementById("stat-funcs");
  const statComments = document.getElementById("stat-comments");

  function calculateCodeStats() {
    if (!codeTextarea) return;
    const text = codeTextarea.value;
    const lines = text ? text.split("\n").length : 0;
    const chars = text.length;

    const funcRegex = /(def\s+[a-zA-Z0-9_]+|function\s+[a-zA-Z0-9_]+|[a-zA-Z0-9_]+\s*\([^)]*\)\s*\{|void\s+[a-zA-Z0-9_]+|int\s+[a-zA-Z0-9_]+)/g;
    const funcMatches = text.match(funcRegex);
    const funcs = funcMatches ? funcMatches.length : 0;

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
    codeTextarea.addEventListener("input", function () {
      calculateCodeStats();
      handlePastedCodeAnalysis();
    });
    codeTextarea.addEventListener("paste", function () {
      setTimeout(() => {
        calculateCodeStats();
        handlePastedCodeAnalysis();
      }, 50);
    });
    codeTextarea.addEventListener("keydown", function (e) {
      if (e.key === "Tab") {
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value = this.value.substring(0, start) + "    " + this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;
        calculateCodeStats();
        handlePastedCodeAnalysis();
      }
    });
  }

  // 7. Live Static Validation Checklist & Submit enabler
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

    const isPaste = (submissionModeInput && submissionModeInput.value === "paste");

    if (isPaste) {
      if (codeTextarea && codeTextarea.value.trim().length > 0) {
        hasCode = true;
        // Auto-detect language if still auto
        if (langSelect && langSelect.value === "auto") {
          const detected = detectLanguageFromCode(codeTextarea.value);
          if (detected) {
            langSelect.value = detected;
            hasLang = true;
          }
        } else if (langSelect && langSelect.value && langSelect.value !== "auto") {
          hasLang = true;
        }
      }
    } else {
      if (fileInput && fileInput.files && fileInput.files.length > 0) {
        hasCode = true;
        if (fileInput.files[0].size > 5 * 1024 * 1024) validSize = false;
        if (langSelect && langSelect.value && langSelect.value !== "auto") hasLang = true;
      } else if (codeTextarea && codeTextarea.value.trim().length > 0) {
        hasCode = true;
        if (langSelect && langSelect.value && langSelect.value !== "auto") hasLang = true;
      }
    }

    if (chkLangName && langSelect) {
      const curVal = langSelect.value;
      chkLangName.textContent = (curVal && curVal !== "auto") ? curVal.toUpperCase() : "Auto-detecting...";
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


});
