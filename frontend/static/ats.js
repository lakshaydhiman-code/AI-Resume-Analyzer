// ==========================================
// ATS Scanner & Job Fit Logic
// ==========================================

const SAMPLE_JDS = {
  fullstack: `Senior Full Stack Developer (React & Python / Node.js)
Responsibilities:
- Build and maintain scalable, robust web applications and microservices.
- Design responsive, modern user interfaces using React, TypeScript, HTML5, and CSS3.
- Develop backend RESTful APIs using Python (FastAPI/Django) or Node.js.
- Work with PostgreSQL, MongoDB, Redis caching, and SQLAlchemy ORM.
- Deploy applications using Docker, Kubernetes, CI/CD pipelines, and AWS (ECS, Lambda, S3).
- Collaborate in an Agile/Scrum environment with cross-functional product teams.
Requirements:
- 3+ years experience with Python or JavaScript/TypeScript.
- Strong proficiency in SQL, database optimization, and system design.
- Hands-on experience with Git, Docker, Unit Testing, and cloud environments.`,

  python_backend: `Lead Backend Engineer (Python / FastAPI / Cloud)
Key Responsibilities:
- Architect high-throughput distributed systems and asynchronous data processing pipelines.
- Build clean REST and GraphQL APIs with FastAPI, Pydantic, and SQLAlchemy.
- Optimize database schemas and queries in PostgreSQL and manage Redis cache clusters.
- Implement CI/CD pipelines using GitHub Actions, Docker, and AWS cloud infrastructure.
- Lead code reviews, enforce best practices, and mentor junior engineers.
Requirements:
- Proven experience with Python, FastAPI/Flask/Django, PostgreSQL, and Redis.
- Knowledge of Microservices architecture, Docker, Kubernetes, and AWS/GCP.
- Strong problem-solving, debugging, and system scalability mindset.`,

  ai_ml: `Machine Learning / AI Engineer
Overview:
We are seeking an AI Engineer to design and deploy state-of-the-art Generative AI and NLP systems.
Key Responsibilities:
- Build LLM-powered applications using Gemini API, LangChain, LlamaIndex, and Vector Databases.
- Develop and fine-tune models with PyTorch, TensorFlow, Scikit-Learn, and Hugging Face.
- Build production data ingestion pipelines with Pandas, NumPy, and SQL.
- Deploy machine learning models into production using FastAPI and Docker on AWS/GCP.
Qualifications:
- Solid background in Python, Deep Learning, NLP, and Artificial Intelligence.
- Experience with REST APIs, cloud deployments, and data science tooling.`,

  devops: `DevOps & Cloud Infrastructure Engineer
Overview:
Looking for a DevOps Engineer to automate and scale our cloud platform.
Responsibilities:
- Build and manage Kubernetes clusters and Docker containers across AWS/GCP.
- Write Infrastructure as Code using Terraform and Ansible.
- Manage CI/CD pipelines with GitHub Actions, Jenkins, and automated testing suites.
- Monitor system health, latency, and logs using Prometheus, Grafana, and CloudWatch.
- Enforce cloud security, IAM policies, and disaster recovery plans.`
};

document.addEventListener("DOMContentLoaded", async () => {
  checkAuth();

  const resumeSelect = document.getElementById("ats-resume-select");
  const jdTextarea = document.getElementById("ats-job-description");
  const analyzeBtn = document.getElementById("btn-analyze-ats");
  const progressCard = document.getElementById("ats-progress-card");
  const resultsCard = document.getElementById("ats-results-card");
  const sampleBtns = document.querySelectorAll(".btn-sample-jd");

  // Sample JD buttons
  sampleBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const type = btn.getAttribute("data-type");
      if (SAMPLE_JDS[type]) {
        jdTextarea.value = SAMPLE_JDS[type];
        showToast("Sample job description loaded!", "info");
      }
    });
  });

  // Load User Resumes into selector
  try {
    const res = await fetchWithAuth("/resume/list");
    if (res.ok) {
      const resumes = await res.json();
      if (resumes.length === 0) {
        resumeSelect.innerHTML = `<option value="">No resumes found - please upload one first</option>`;
        analyzeBtn.disabled = true;
      } else {
        const urlParams = new URLSearchParams(window.location.search);
        const preselectedId = urlParams.get("resume_id");

        resumeSelect.innerHTML = resumes.map((r, idx) => {
          const isSelected = preselectedId ? (r.id.toString() === preselectedId) : (idx === 0);
          return `<option value="${r.id}" ${isSelected ? "selected" : ""}>${r.file_name} (${r.candidate_name || "Profile"} - ${r.profile_score}%)</option>`;
        }).join("");
      }
    }
  } catch (err) {
    console.error("Failed to load resumes for ATS:", err);
  }

  // Analyze Button
  analyzeBtn.addEventListener("click", async () => {
    const resumeId = resumeSelect.value;
    const jdText = jdTextarea.value.trim();

    if (!resumeId) {
      showToast("Please select a resume to analyze.", "warning");
      return;
    }
    if (!jdText || jdText.length < 20) {
      showToast("Please paste a comprehensive job description (at least 20 characters).", "warning");
      return;
    }

    analyzeBtn.disabled = true;
    if (progressCard) progressCard.style.display = "block";
    if (resultsCard) resultsCard.style.display = "none";

    try {
      const response = await fetchWithAuth("/ats/analyze", {
        method: "POST",
        body: JSON.stringify({
          resume_id: parseInt(resumeId),
          job_description: jdText
        })
      });

      const data = await response.json();
      if (response.ok) {
        showToast("ATS Analysis completed!", "success");
        if (progressCard) progressCard.style.display = "none";
        renderATSResults(data);
      } else {
        if (progressCard) progressCard.style.display = "none";
        showToast(data.detail || "ATS analysis failed.", "error");
      }
    } catch (err) {
      if (progressCard) progressCard.style.display = "none";
      showToast(err.message || "An error occurred during ATS analysis.", "error");
    } finally {
      analyzeBtn.disabled = false;
    }
  });

  function renderATSResults(data) {
    if (!resultsCard) return;
    resultsCard.style.display = "block";

    const score = data.ats_score || 0;

    // Score Gauge
    const scoreGauge = document.getElementById("ats-score-gauge");
    const scoreNum = document.getElementById("ats-score-num");
    if (scoreGauge) {
      const ringColor = score >= 75 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
      scoreGauge.style.setProperty("--score", score);
      scoreGauge.style.setProperty("--score-color", ringColor);
    }
    if (scoreNum) scoreNum.textContent = score;

    // Job Title Detected
    const titleBadge = document.getElementById("ats-job-title-badge");
    if (titleBadge) {
      titleBadge.textContent = data.job_title_detected || "Target Position";
    }

    // Matched Skills
    const matchedSkillsEl = document.getElementById("ats-matched-skills");
    if (matchedSkillsEl) {
      const skills = data.matched_skills || [];
      if (skills.length > 0) {
        matchedSkillsEl.innerHTML = skills.map(s => `<span class="tag tag-success">✓ ${s}</span>`).join("");
      } else {
        matchedSkillsEl.innerHTML = `<span style="color: var(--text-dim); font-size: 0.85rem;">No direct matching skills found.</span>`;
      }
    }

    // Missing Skills
    const missingSkillsEl = document.getElementById("ats-missing-skills");
    if (missingSkillsEl) {
      const skills = data.missing_skills || [];
      if (skills.length > 0) {
        missingSkillsEl.innerHTML = skills.map(s => `<span class="tag tag-danger">+ ${s}</span>`).join("");
      } else {
        missingSkillsEl.innerHTML = `<span style="color: var(--success); font-size: 0.85rem;">Great job! You have all major required skills.</span>`;
      }
    }

    // Matched Keywords
    const matchedKwEl = document.getElementById("ats-matched-keywords");
    if (matchedKwEl) {
      const kws = data.matched_keywords || [];
      if (kws.length > 0) {
        matchedKwEl.innerHTML = kws.map(k => `<span class="tag tag-primary">✓ ${k}</span>`).join("");
      } else {
        matchedKwEl.innerHTML = `<span style="color: var(--text-dim); font-size: 0.85rem;">No strategic keywords matched.</span>`;
      }
    }

    // Missing Keywords
    const missingKwEl = document.getElementById("ats-missing-keywords");
    if (missingKwEl) {
      const kws = data.missing_keywords || [];
      if (kws.length > 0) {
        missingKwEl.innerHTML = kws.map(k => `<span class="tag tag-warning">⚠ ${k}</span>`).join("");
      } else {
        missingKwEl.innerHTML = `<span style="color: var(--success); font-size: 0.85rem;">Keywords coverage is excellent.</span>`;
      }
    }

    // Strengths
    const strengthsEl = document.getElementById("ats-strengths-list");
    if (strengthsEl) {
      const strengths = data.strengths || [];
      if (strengths.length > 0) {
        strengthsEl.innerHTML = strengths.map(s => `<li style="margin-bottom: 0.5rem; color: #a7f3d0;">${s}</li>`).join("");
      } else {
        strengthsEl.innerHTML = `<li>Solid overall profile foundation.</li>`;
      }
    }

    // Improvement Suggestions
    const suggestionsEl = document.getElementById("ats-suggestions-list");
    if (suggestionsEl) {
      const suggestions = data.improvement_suggestions || [];
      if (suggestions.length > 0) {
        suggestionsEl.innerHTML = suggestions.map(s => `<li style="margin-bottom: 0.65rem; color: #fde68a;">${s}</li>`).join("");
      } else {
        suggestionsEl.innerHTML = `<li>Resume aligns well with standard requirements.</li>`;
      }
    }

    // Summary Assessment
    const summaryEl = document.getElementById("ats-summary-assessment");
    if (summaryEl) {
      summaryEl.textContent = data.summary_assessment || "No detailed summary available.";
    }

    // Ask AI button
    const btnChatAts = document.getElementById("btn-chat-ats-advice");
    if (btnChatAts && data.resume_id) {
      btnChatAts.href = `/chat.html?resume_id=${data.resume_id}`;
    }

    resultsCard.scrollIntoView({ behavior: "smooth" });
  }
});
