// ==========================================
// Dashboard Logic
// ==========================================

document.addEventListener("DOMContentLoaded", async () => {
  checkAuth();

  const totalResumesEl = document.getElementById("stat-total-resumes");
  const latestScoreEl = document.getElementById("stat-latest-score");
  const atsStatusEl = document.getElementById("stat-ats-status");
  const latestResumeCard = document.getElementById("latest-resume-card");
  const emptyStateCard = document.getElementById("empty-state-card");
  const recentResumesList = document.getElementById("recent-resumes-list");

  try {
    // 1. Fetch user resume list
    const res = await fetchWithAuth("/resume/list");
    if (!res.ok) throw new Error("Failed to load resumes");
    const resumes = await res.json();

    if (totalResumesEl) totalResumesEl.textContent = resumes.length;

    if (resumes.length === 0) {
      if (latestScoreEl) latestScoreEl.textContent = "--";
      if (atsStatusEl) atsStatusEl.textContent = "No Data";
      if (emptyStateCard) emptyStateCard.style.display = "block";
      if (latestResumeCard) latestResumeCard.style.display = "none";
      if (recentResumesList) {
        recentResumesList.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-dim); padding: 2rem;">No resumes uploaded yet. Click "Upload Resume" to get started!</td></tr>`;
      }
      return;
    }

    // 2. Fetch detailed latest resume
    const latestRes = await fetchWithAuth("/resume/latest");
    if (latestRes.ok) {
      const latestData = await latestRes.json();
      const score = latestData.profile_score || 0;
      const parsed = latestData.parsed_data || {};

      if (latestScoreEl) latestScoreEl.textContent = `${score}/100`;

      let atsBadge = "Ready";
      let atsColor = "#10b981";
      if (score < 50) {
        atsBadge = "Needs Work";
        atsColor = "#ef4444";
      } else if (score < 75) {
        atsBadge = "Moderate";
        atsColor = "#f59e0b";
      }
      if (atsStatusEl) {
        atsStatusEl.innerHTML = `<span style="color: ${atsColor}; font-weight: 700;">${atsBadge}</span>`;
      }

      // Update Gauge Ring
      const gaugeRing = document.getElementById("dashboard-score-gauge");
      if (gaugeRing) {
        let ringColor = score >= 75 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
        gaugeRing.style.setProperty("--score", score);
        gaugeRing.style.setProperty("--score-color", ringColor);
      }
      const gaugeNum = document.getElementById("dashboard-score-num");
      if (gaugeNum) gaugeNum.textContent = score;

      // Populate Latest Resume Card
      if (emptyStateCard) emptyStateCard.style.display = "none";
      if (latestResumeCard) {
        latestResumeCard.style.display = "block";

        const candName = document.getElementById("latest-cand-name");
        const candFile = document.getElementById("latest-file-name");
        const candEmail = document.getElementById("latest-cand-email");
        const candPhone = document.getElementById("latest-cand-phone");
        const candSummary = document.getElementById("latest-cand-summary");
        const candSkills = document.getElementById("latest-cand-skills");
        const downloadBtn = document.getElementById("btn-download-latest");
        const atsBtn = document.getElementById("btn-ats-latest");

        if (candName) candName.textContent = parsed.name || "Candidate Name";
        if (candFile) candFile.textContent = latestData.file_name || "";
        if (candEmail) candEmail.textContent = parsed.email || "No email listed";
        if (candPhone) candPhone.textContent = parsed.phone || "No phone listed";
        if (candSummary) candSummary.textContent = parsed.summary || "No professional summary provided.";

        if (candSkills) {
          const skillsList = parsed.skills || [];
          if (skillsList.length > 0) {
            candSkills.innerHTML = skillsList.slice(0, 10).map(s => `<span class="tag tag-primary">${s}</span>`).join("");
            if (skillsList.length > 10) {
              candSkills.innerHTML += `<span class="tag">+${skillsList.length - 10} more</span>`;
            }
          } else {
            candSkills.innerHTML = `<span style="color: var(--text-dim); font-size: 0.85rem;">No specific skills extracted.</span>`;
          }
        }

        if (downloadBtn) {
          downloadBtn.href = `/resume/${latestData.id}/download`;
        }
        if (atsBtn) {
          atsBtn.href = `/ats.html?resume_id=${latestData.id}`;
        }
      }
    }

    // Populate Recent Resumes Table (top 4)
    if (recentResumesList) {
      recentResumesList.innerHTML = resumes.slice(0, 4).map(r => {
        const dateStr = new Date(r.created_at).toLocaleDateString(undefined, {
          month: "short", day: "numeric", year: "numeric"
        });
        const scoreBadge = r.profile_score >= 75 ? "tag-success" : r.profile_score >= 50 ? "tag-primary" : "tag-danger";
        return `
          <tr>
            <td>
              <div style="font-weight: 600;">${r.file_name}</div>
              <div style="font-size: 0.75rem; color: var(--text-dim);">${r.candidate_name || "Parsed Candidate"}</div>
            </td>
            <td>${dateStr}</td>
            <td><span class="tag ${scoreBadge}">${r.profile_score}%</span></td>
            <td><span class="tag">${r.skills_count} skills</span></td>
            <td>
              <div style="display: flex; gap: 0.5rem;">
                <a href="/ats.html?resume_id=${r.id}" class="btn btn-outline btn-sm">ATS Check</a>
                <a href="/resume/${r.id}/download" class="btn btn-secondary btn-sm">Download</a>
              </div>
            </td>
          </tr>
        `;
      }).join("");
    }

  } catch (err) {
    console.error("Dashboard error:", err);
    showToast("Failed to load dashboard data.", "error");
  }
});
