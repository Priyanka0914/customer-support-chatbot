const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const log = document.getElementById("chat-log");

// Persist the session ID across messages (and page reloads) so the backend
// can remember multi-turn context, e.g. "waiting for an order ID".
function getSessionId() {
  let id = localStorage.getItem("chat_session_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("chat_session_id", id);
  }
  return id;
}

function addMessage(text, sender) {
  const div = document.createElement("div");
  div.className = sender === "user" ? "user-msg" : "bot-msg";
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  addMessage(message, "user");
  input.value = "";

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: getSessionId() }),
    });
    const data = await res.json();
    addMessage(data.response || data.error || "Something went wrong.", "bot");
  } catch (err) {
    addMessage("Could not reach the server. Is the Flask app running?", "bot");
  }
});
