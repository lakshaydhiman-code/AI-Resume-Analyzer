// ==========================================
// Resume Upload & Live Parsing Logic
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
  checkAuth();

  const dropzone = document.getElementById("upload-dropzone");
  const fileInput = document.getElementById("file-input");
  const fileInfoCard = document.getElementById("file-info-card");
  const fileNameDisplay = document.getElementById("selected-file-name");
  const fileSizeDisplay = document.getElementById("selected-file-size");
  const uploadForm = document.getElementById("upload-form");
  const uploadBtn = document.getElementById("btn-upload-submit");
  const uploadProgress = document.getElementById("upload-progress-card");
  const statusStep = document.getElementById("upload-status-step");
  const resultCard = document.getElementById("upload-result-card");

  let selectedFile = null;

  function handleFileSelection(file) {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      showToast("Only PDF files are supported. Please select a .pdf file.", "error");
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      showToast("File size exceeds 15MB limit. Please upload a smaller PDF.", "error");
      return;
    }

    selectedFile = file;
    if (fileNameDisplay) fileNameDisplay.textContent = file.name;
    if (fileSizeDisplay) fileSizeDisplay.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
    if (fileInfoCard) fileInfoCard.style.display = "flex";
    if (uploadBtn) uploadBtn.disabled = false;
  }

  // Drag & Drop
  if (dropzone) {
    ["dragenter", "dragover"].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("dragover");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        handleFileSelection(files[0]);
      }
    });

    dropzone.addEventListener("click", () => {
      fileInput.click();
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelection(e.target.files[0]);
      }
    });
  }

  // Form Submit
  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!selectedFile) {
        showToast("Please choose a PDF resume file first.", "warning");
        return;
      }

      const formData = new FormData();
      formData.append("file", selectedFile);

      if (uploadBtn) uploadBtn.disabled = true;
      if (uploadProgress) uploadProgress.style.display = "block";
      if (resultCard) resultCard.style.display = "none";

      // Simulated realistic status step transitions
      const steps = [
        "1/4: Reading document text with PyMuPDF...",
        "2/4: Checking OCR layer for scanned elements...",
        "3/4: Analyzing and parsing resume sections with AI...",
        "4/4: Calculating profile score and generating insights..."
      ];
      let stepIdx = 0;
      if (statusStep) statusStep.textContent = steps[0];
      const stepInterval = setInterval(() => {
        stepIdx = (stepIdx + 1) % steps.length;
        if (statusStep) statusStep.textContent = steps[stepIdx];
      }, 1200);

      try {
        const response = await fetchWithAuth("/resume/upload", {
          method: "POST",
          body: formData
        });

        clearInterval(stepInterval);
        const data = await response.json();

        if (response.ok && data.success) {
          showToast("Resume parsed successfully!", "success");
          if (uploadProgress) uploadProgress.style.display = "none";
          renderParsedResults(data);
        } else {
          if (uploadProgress) uploadProgress.style.display = "none";
          showToast(data.detail || "Failed to process resume.", "error");
        }
      } catch (err) {
        clearInterval(stepInterval);
        if (uploadProgress) uploadProgress.style.display = "none";
        showToast(err.message || "An error occurred during upload.", "error");
      } finally {
        if (uploadBtn) uploadBtn.disabled = false;
      }
    });
  }

  function renderParsedResults(data) {
    if (!resultCard) return;
    resultCard.style.display = "block";

    const parsed = data.resume || {};
    const score = data.profile_score || 0;

    // Score Gauge
    const scoreGauge = document.getElementById("result-score-gauge");
    const scoreNum = document.getElementById("result-score-num");
    if (scoreGauge) {
      const ringColor = score >= 75 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
      scoreGauge.style.setProperty("--score", score);
      scoreGauge.style.setProperty("--score-color", ringColor);
    }
    if (scoreNum) scoreNum.textContent = score;

    // Contact info
    const resName = document.getElementById("res-name");
    const resEmail = document.getElementById("res-email");
    const resPhone = document.getElementById("res-phone");
    const resSummary = document.getElementById("res-summary");
    const resSkills = document.getElementById("res-skills");

    if (resName) resName.textContent = parsed.name || "Candidate Profile";
    if (resEmail) resEmail.textContent = parsed.email || "Not specified";
    if (resPhone) resPhone.textContent = parsed.phone || "Not specified";
    if (resSummary) resSummary.textContent = parsed.summary || "No professional summary extracted.";

    // Skills
    if (resSkills) {
      const skills = parsed.skills || [];
      if (skills.length > 0) {
        resSkills.innerHTML = skills.map(s => `<span class="tag tag-primary">${s}</span>`).join("");
      } else {
        resSkills.innerHTML = `<span style="color: var(--text-dim);">No skills identified.</span>`;
      }
    }

    // Experience
    const resExp = document.getElementById("res-experience");
    if (resExp) {
      const expList = parsed.experience || [];
      if (expList.length > 0) {
        resExp.innerHTML = expList.map(exp => {
          if (typeof exp === "string") {
            return `<div style="margin-bottom: 0.75rem; padding-left: 1rem; border-left: 2px solid var(--primary);">${exp}</div>`;
          }
          const highlights = Array.isArray(exp.highlights) ? exp.highlights.map(h => `<li>${h}</li>`).join("") : "";
          return `
            <div style="background: rgba(255,255,255,0.03); padding: 1.25rem; border-radius: var(--radius-sm); margin-bottom: 1rem; border: 1px solid var(--border-color);">
              <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <div style="font-weight: 700; font-size: 1.05rem; color: #fff;">${exp.title || "Role"}</div>
                <div style="font-size: 0.85rem; color: var(--text-dim);">${exp.duration || ""}</div>
              </div>
              <div style="color: var(--primary); font-size: 0.9rem; margin-bottom: 0.5rem;">${exp.company || ""}${exp.location ? " • " + exp.location : ""}</div>
              ${highlights ? `<ul style="padding-left: 1.25rem; color: var(--text-muted); font-size: 0.9rem;">${highlights}</ul>` : ""}
            </div>
          `;
        }).join("");
      } else {
        resExp.innerHTML = `<div style="color: var(--text-dim);">No work experience entries extracted.</div>`;
      }
    }

    // Education
    const resEdu = document.getElementById("res-education");
    if (resEdu) {
      const eduList = parsed.education || [];
      if (eduList.length > 0) {
        resEdu.innerHTML = eduList.map(edu => {
          if (typeof edu === "string") {
            return `<div style="margin-bottom: 0.5rem;">${edu}</div>`;
          }
          return `
            <div style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: var(--radius-sm); margin-bottom: 0.75rem; border: 1px solid var(--border-color);">
              <div style="font-weight: 700; color: #fff;">${edu.degree || "Degree"}</div>
              <div style="color: var(--text-muted); font-size: 0.9rem;">${edu.institution || ""}${edu.year ? " • " + edu.year : ""} ${edu.gpa ? "(GPA: " + edu.gpa + ")" : ""}</div>
            </div>
          `;
        }).join("");
      } else {
        resEdu.innerHTML = `<div style="color: var(--text-dim);">No education records extracted.</div>`;
      }
    }

    // Projects
    const resProj = document.getElementById("res-projects");
    if (resProj) {
      const projList = parsed.projects || [];
      if (projList.length > 0) {
        resProj.innerHTML = projList.map(p => {
          if (typeof p === "string") return `<div>${p}</div>`;
          return `
            <div style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: var(--radius-sm); margin-bottom: 0.75rem; border: 1px solid var(--border-color);">
              <div style="font-weight: 700; color: #fff;">${p.name || "Project"}</div>
              ${p.tech_stack ? `<div style="font-size: 0.825rem; color: var(--primary); margin: 0.2rem 0;">Tech: ${p.tech_stack}</div>` : ""}
              <div style="color: var(--text-muted); font-size: 0.9rem;">${p.description || ""}</div>
              ${p.link ? `<a href="${p.link}" target="_blank" style="font-size: 0.85rem; margin-top: 0.4rem; display: inline-block;">View Project ↗</a>` : ""}
            </div>
          `;
        }).join("");
      } else {
        resProj.innerHTML = `<div style="color: var(--text-dim);">No projects extracted.</div>`;
      }
    }

    // Certifications
    const resCerts = document.getElementById("res-certifications");
    if (resCerts) {
      const certList = parsed.certifications || [];
      if (certList.length > 0) {
        resCerts.innerHTML = certList.map(c => `<span class="tag tag-success">📜 ${c}</span>`).join("");
      } else {
        resCerts.innerHTML = `<span style="color: var(--text-dim);">No certifications found.</span>`;
      }
    }

    // Setup action buttons
    const btnAts = document.getElementById("btn-goto-ats");
    const btnChat = document.getElementById("btn-goto-chat");
    if (btnAts) btnAts.href = `/ats.html?resume_id=${data.resume_id}`;
    if (btnChat) btnChat.href = `/chat.html?resume_id=${data.resume_id}`;

    // Smooth scroll down to results
    resultCard.scrollIntoView({ behavior: "smooth" });
  }
});
