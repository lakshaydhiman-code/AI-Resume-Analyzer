// ==========================================
// Resume Management Logic
// ==========================================

document.addEventListener("DOMContentLoaded", async () => {
  checkAuth();

  const resumesTableBody = document.getElementById("resumes-table-body");
  const emptyState = document.getElementById("resumes-empty-state");
  const modal = document.getElementById("resume-detail-modal");
  const modalCloseBtn = document.getElementById("modal-close-btn");

  async function loadResumes() {
    try {
      const res = await fetchWithAuth("/resume/list");
      if (!res.ok) throw new Error("Failed to load resumes.");
      const resumes = await res.json();

      if (resumes.length === 0) {
        if (emptyState) emptyState.style.display = "block";
        if (resumesTableBody) resumesTableBody.innerHTML = "";
        return;
      }

      if (emptyState) emptyState.style.display = "none";
      if (resumesTableBody) {
        resumesTableBody.innerHTML = resumes.map(r => {
          const dateStr = new Date(r.created_at).toLocaleDateString(undefined, {
            month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit"
          });
          const scoreClass = r.profile_score >= 75 ? "tag-success" : r.profile_score >= 50 ? "tag-primary" : "tag-danger";

          return `
            <tr id="resume-row-${r.id}">
              <td>
                <div style="font-weight: 600; color: #fff;">${r.file_name}</div>
                <div style="font-size: 0.8rem; color: var(--text-dim);">${r.candidate_name || "Profile"}</div>
              </td>
              <td>${dateStr}</td>
              <td><span class="tag ${scoreClass}">${r.profile_score}%</span></td>
              <td><span class="tag">${r.skills_count} skills</span></td>
              <td>
                <div style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
                  <button class="btn btn-primary btn-sm btn-view-resume" data-id="${r.id}">View</button>
                  <a href="/ats.html?resume_id=${r.id}" class="btn btn-outline btn-sm">ATS</a>
                  <a href="/chat.html?resume_id=${r.id}" class="btn btn-outline btn-sm">Chat</a>
                  <a href="/resume/${r.id}/download" class="btn btn-secondary btn-sm" title="Download original PDF">⬇</a>
                  <button class="btn btn-danger btn-sm btn-delete-resume" data-id="${r.id}" data-name="${r.file_name}" title="Delete resume">🗑</button>
                </div>
              </td>
            </tr>
          `;
        }).join("");

        attachActionListeners();
      }
    } catch (err) {
      console.error(err);
      showToast("Could not load resumes list.", "error");
    }
  }

  function attachActionListeners() {
    // View Details Modal
    document.querySelectorAll(".btn-view-resume").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-id");
        openDetailModal(id);
      });
    });

    // Delete Resume
    document.querySelectorAll(".btn-delete-resume").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-id");
        const name = btn.getAttribute("data-name");

        if (confirm(`Are you sure you want to permanently delete "${name}"?`)) {
          try {
            const res = await fetchWithAuth(`/resume/${id}`, { method: "DELETE" });
            const data = await res.json();
            if (res.ok) {
              showToast("Resume deleted successfully.", "success");
              loadResumes();
            } else {
              showToast(data.detail || "Failed to delete resume.", "error");
            }
          } catch (e) {
            showToast("Error deleting resume.", "error");
          }
        }
      });
    });
  }

  async function openDetailModal(id) {
    if (!modal) return;
    modal.classList.add("active");

    const modalBody = document.getElementById("modal-resume-body");
    const modalTitle = document.getElementById("modal-resume-title");
    modalBody.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading resume details...</div>`;

    try {
      const res = await fetchWithAuth(`/resume/${id}`);
      if (!res.ok) throw new Error("Could not retrieve resume details");
      const data = await res.json();
      const parsed = data.parsed_data || {};

      if (modalTitle) modalTitle.textContent = `${data.file_name} (${data.profile_score}% Score)`;

      const skillsHtml = (parsed.skills || []).map(s => `<span class="tag tag-primary">${s}</span>`).join("") || `<span style="color: var(--text-dim);">None</span>`;

      const expHtml = (parsed.experience || []).map(e => {
        if (typeof e === "string") return `<li>${e}</li>`;
        return `
          <div style="margin-bottom: 0.75rem; padding: 0.75rem; background: rgba(255,255,255,0.02); border-radius: var(--radius-sm);">
            <div style="font-weight: 600; color: #fff;">${e.title || "Role"} • <span style="color: var(--primary);">${e.company || ""}</span></div>
            <div style="font-size: 0.8rem; color: var(--text-dim);">${e.duration || ""}</div>
            ${e.highlights ? `<ul style="padding-left: 1.25rem; font-size: 0.875rem; margin-top: 0.35rem;">${(e.highlights || []).map(h => `<li>${h}</li>`).join("")}</ul>` : ""}
          </div>
        `;
      }).join("") || `<div style="color: var(--text-dim);">No experience entries.</div>`;

      const eduHtml = (parsed.education || []).map(ed => {
        if (typeof ed === "string") return `<div>${ed}</div>`;
        return `<div style="margin-bottom: 0.5rem;"><strong>${ed.degree || "Degree"}</strong> - ${ed.institution || ""} ${ed.year ? "(" + ed.year + ")" : ""}</div>`;
      }).join("") || `<div style="color: var(--text-dim);">No education records.</div>`;

      const projHtml = (parsed.projects || []).map(p => {
        if (typeof p === "string") return `<div>${p}</div>`;
        return `<div style="margin-bottom: 0.5rem;"><strong>${p.name || "Project"}</strong>: ${p.description || ""}</div>`;
      }).join("") || `<div style="color: var(--text-dim);">No projects listed.</div>`;

      const certHtml = (parsed.certifications || []).map(c => `<span class="tag tag-success">📜 ${c}</span>`).join("") || `<span style="color: var(--text-dim);">None</span>`;

      modalBody.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
          <div>
            <div style="font-size: 0.8rem; color: var(--text-dim);">Candidate Name</div>
            <div style="font-weight: 700; font-size: 1.1rem; color: #fff;">${parsed.name || "N/A"}</div>
          </div>
          <div>
            <div style="font-size: 0.8rem; color: var(--text-dim);">Contact Info</div>
            <div style="font-size: 0.9rem;">${parsed.email || "N/A"} • ${parsed.phone || "N/A"}</div>
          </div>
        </div>

        <div style="margin-bottom: 1.25rem;">
          <h4 style="color: var(--text-muted); margin-bottom: 0.4rem;">Professional Summary</h4>
          <p style="background: rgba(255,255,255,0.02); padding: 0.75rem; border-radius: var(--radius-sm); font-size: 0.9rem;">
            ${parsed.summary || "No summary provided."}
          </p>
        </div>

        <div style="margin-bottom: 1.25rem;">
          <h4 style="color: var(--text-muted); margin-bottom: 0.4rem;">Extracted Skills</h4>
          <div class="tag-container">${skillsHtml}</div>
        </div>

        <div style="margin-bottom: 1.25rem;">
          <h4 style="color: var(--text-muted); margin-bottom: 0.4rem;">Experience</h4>
          <div>${expHtml}</div>
        </div>

        <div style="margin-bottom: 1.25rem;">
          <h4 style="color: var(--text-muted); margin-bottom: 0.4rem;">Education</h4>
          <div>${eduHtml}</div>
        </div>

        <div style="margin-bottom: 1.25rem;">
          <h4 style="color: var(--text-muted); margin-bottom: 0.4rem;">Projects</h4>
          <div>${projHtml}</div>
        </div>

        <div style="margin-bottom: 1.5rem;">
          <h4 style="color: var(--text-muted); margin-bottom: 0.4rem;">Certifications</h4>
          <div class="tag-container">${certHtml}</div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">
          <a href="/resume/${id}/download" class="btn btn-secondary">Download PDF</a>
          <a href="/ats.html?resume_id=${id}" class="btn btn-primary">Run ATS Match</a>
        </div>
      `;

    } catch (e) {
      modalBody.innerHTML = `<div style="color: var(--danger); text-align: center;">Failed to load resume details.</div>`;
    }
  }

  // Close modal
  if (modalCloseBtn) {
    modalCloseBtn.addEventListener("click", () => {
      if (modal) modal.classList.remove("active");
    });
  }
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal && modal.classList.contains("active")) {
      modal.classList.remove("active");
    }
  });

  // Init
  loadResumes();
});
