const API_BASE = "http://127.0.0.1:8000";
const form = document.getElementById("chatForm");
const input = document.getElementById("userInput");
const chatArea = document.getElementById("chatArea");
const emptyState = document.getElementById("emptyState");
const newChat = document.getElementById("newChat");
let history = [];

function addMessage(role, text, status = "") {
  if (emptyState) emptyState.style.display = "none";
  const row = document.createElement("div");
  row.className = `message ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = role === "assistant" ? "TC" : "YOU";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (status) {
    const statusEl = document.createElement("div");
    statusEl.className = `status ${status}`;
    statusEl.textContent = ({
      verified: "✓ VERIFIED FROM SAMPLE CATALOGUE",
      clarify: "? CLARIFICATION NEEDED",
      refuse: "! UNSUPPORTED CLAIM REFUSED",
      info: "ℹ PREFERENCES UPDATED"
    })[status] || status.toUpperCase();
    bubble.appendChild(statusEl);
  }
  const content = document.createElement("div");
  content.textContent = text;
  bubble.appendChild(content);
  row.appendChild(avatar);
  row.appendChild(bubble);
  chatArea.appendChild(row);
  chatArea.scrollTop = chatArea.scrollHeight;
}

async function sendMessage(query) {
  const trimmed = query.trim();
  if (!trimmed) return;
  addMessage("user", trimmed);
  input.value = "";
  history.push({role: "user", content: trimmed});
  const waiting = document.createElement("div");
  waiting.className = "message assistant";
  waiting.innerHTML = '<div class="msg-avatar">TC</div><div class="bubble">Checking available evidence…</div>';
  chatArea.appendChild(waiting);
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({query: trimmed, history})
    });
    if (!response.ok) throw new Error("Backend returned an error");
    const data = await response.json();
    waiting.remove();
    addMessage("assistant", data.answer, data.status);
    history.push({role: "assistant", content: data.answer});
  } catch (error) {
    waiting.remove();
    addMessage("assistant", "I can’t reach the local Python backend. Start it in VS Code with: uvicorn main:app --reload", "refuse");
  }
}

form.addEventListener("submit", event => {
  event.preventDefault();
  sendMessage(input.value);
});
document.querySelectorAll("[data-query]").forEach(button => {
  button.addEventListener("click", () => sendMessage(button.dataset.query));
});
newChat.addEventListener("click", () => {
  history = [];
  chatArea.innerHTML = "";
  const state = document.createElement("div");
  state.className = "empty-state";
  state.innerHTML = '<h3>What are you looking for?</h3><p>Try a product, a price question, or ask about the return policy.</p>';
  chatArea.appendChild(state);
});
