// ==========================================
// AI Career Assistant Chat Logic
// ==========================================

let conversationHistory = [];

document.addEventListener("DOMContentLoaded", async () => {
  checkAuth();

  const resumeSelect = document.getElementById("chat-resume-select");
  const chatMessages = document.getElementById("chat-messages");
  const chatInput = document.getElementById("chat-input");
  const sendBtn = document.getElementById("btn-send-chat");
  const quickPromptBtns = document.querySelectorAll(".btn-quick-prompt");
  const clearChatBtn = document.getElementById("btn-clear-chat");

  // Load User Resumes for Context
  try {
    const res = await fetchWithAuth("/resume/list");
    if (res.ok) {
      const resumes = await res.json();
      if (resumes.length === 0) {
        resumeSelect.innerHTML = `<option value="">General Advice (No resumes uploaded)</option>`;
      } else {
        const urlParams = new URLSearchParams(window.location.search);
        const preselectedId = urlParams.get("resume_id");

        resumeSelect.innerHTML = resumes.map((r, idx) => {
          const isSelected = preselectedId ? (r.id.toString() === preselectedId) : (idx === 0);
          return `<option value="${r.id}" ${isSelected ? "selected" : ""}>Context: ${r.file_name} (${r.candidate_name || "Profile"})</option>`;
        }).join("");
      }
    }
  } catch (e) {
    console.error("Failed to load chat resume context:", e);
  }

  // Markdown formatter helper
  function formatMarkdown(text) {
    if (!text) return "";
    let html = text
      .replace(/### (.*?)\n/g, '<h3 style="color: #fff; margin: 0.75rem 0 0.4rem 0; font-size: 1.1rem;">$1</h3>')
      .replace(/## (.*?)\n/g, '<h2 style="color: #fff; margin: 0.75rem 0 0.4rem 0; font-size: 1.25rem;">$1</h2>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code style="background: rgba(255,255,255,0.1); padding: 0.1rem 0.3rem; border-radius: 4px; font-family: monospace;">$1</code>')
      .replace(/\n\n/g, '</p><p style="margin-top: 0.5rem;">')
      .replace(/^\s*-\s+(.*?)$/gm, '<li style="margin-left: 1.25rem;">$1</li>')
      .replace(/^\s*\*\s+(.*?)$/gm, '<li style="margin-left: 1.25rem;">$1</li>')
      .replace(/^\s*\d+\.\s+(.*?)$/gm, '<li style="margin-left: 1.25rem;">$1</li>');
    return `<p>${html}</p>`;
  }

  function appendMessage(role, content) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "chat-avatar";
    avatar.textContent = role === "user" ? "You" : "AI";

    const textDiv = document.createElement("div");
    textDiv.className = "chat-text";
    textDiv.innerHTML = role === "user" ? `<p>${content}</p>` : formatMarkdown(content);

    bubble.appendChild(avatar);
    bubble.appendChild(textDiv);
    chatMessages.appendChild(bubble);

    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendTypingIndicator() {
    const indicator = document.createElement("div");
    indicator.id = "typing-indicator";
    indicator.className = "chat-bubble assistant";
    indicator.innerHTML = `
      <div class="chat-avatar">AI</div>
      <div class="chat-text" style="color: var(--text-muted); font-style: italic;">
        Thinking and analyzing your resume context...
      </div>
    `;
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function removeTypingIndicator() {
    const ind = document.getElementById("typing-indicator");
    if (ind) ind.remove();
  }

  async function handleSendMessage(messageText) {
    const text = messageText || chatInput.value.trim();
    if (!text) return;

    appendMessage("user", text);
    conversationHistory.push({ role: "user", content: text });
    chatInput.value = "";

    appendTypingIndicator();
    sendBtn.disabled = true;

    const resumeIdVal = resumeSelect.value ? parseInt(resumeSelect.value) : null;

    try {
      const res = await fetchWithAuth("/chat/message", {
        method: "POST",
        body: JSON.stringify({
          message: text,
          resume_id: resumeIdVal,
          history: conversationHistory
        })
      });

      removeTypingIndicator();
      const data = await res.json();

      if (res.ok && data.reply) {
        appendMessage("assistant", data.reply);
        conversationHistory.push({ role: "assistant", content: data.reply });
      } else {
        appendMessage("assistant", "I encountered an issue processing your question. Please try again.");
      }
    } catch (err) {
      removeTypingIndicator();
      appendMessage("assistant", "Sorry, a network connection error occurred.");
    } finally {
      sendBtn.disabled = false;
      chatInput.focus();
    }
  }

  // Event Listeners
  if (sendBtn) {
    sendBtn.addEventListener("click", () => handleSendMessage());
  }

  if (chatInput) {
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });
  }

  quickPromptBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const promptText = btn.getAttribute("data-prompt") || btn.textContent.trim();
      handleSendMessage(promptText);
    });
  });

  if (clearChatBtn) {
    clearChatBtn.addEventListener("click", () => {
      conversationHistory = [];
      chatMessages.innerHTML = `
        <div class="chat-bubble assistant">
          <div class="chat-avatar">AI</div>
          <div class="chat-text">
            <p>Hello! I am your <strong>ResumeLab AI Career Assistant</strong>.</p>
            <p style="margin-top: 0.4rem;">I can help you polish bullet points in <strong>STAR format</strong>, discover missing keywords, target specific job roles, and prepare for interviews based on your uploaded resume.</p>
          </div>
        </div>
      `;
      showToast("Chat conversation cleared.", "info");
    });
  }
});
