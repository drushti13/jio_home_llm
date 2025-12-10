const API_URL = "http://127.0.0.1:8000/ask";

const chatbox = document.getElementById("chatbox");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

function linkify(text) {
  // Convert plain URLs into clickable links
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  return text.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');
}

function appendMessage(text, sender, sources = []) {
  const row = document.createElement("div");
  row.classList.add("message-row", sender);

  const bubble = document.createElement("div");
  bubble.classList.add("message-bubble", sender);

  if (sender === "bot") {
    // ✅ Markdown → HTML conversion
    const renderedHTML = marked.parse(linkify(text));
    bubble.innerHTML = renderedHTML;
  } else {
    bubble.textContent = text; // Keep user text plain
  }

  row.appendChild(bubble);

  // Add source chips (optional UI)
  if (sender === "bot" && sources && sources.length > 0) {
    const bar = document.createElement("div");
    bar.classList.add("sources-bar");

    sources.forEach((url, idx) => {
      const chip = document.createElement("div");
      chip.classList.add("source-chip");
      chip.textContent = `Source ${idx + 1}`;
      chip.title = url;
      chip.onclick = () => window.open(url, "_blank");
      bar.appendChild(chip);
    });

    bubble.appendChild(bar);
  }

  chatbox.appendChild(row);
  chatbox.scrollTop = chatbox.scrollHeight;
}

function appendTypingIndicator() {
  const row = document.createElement("div");
  row.classList.add("message-row", "bot");
  row.id = "typing-row";

  const bubble = document.createElement("div");
  bubble.classList.add("message-bubble", "bot");

  const label = document.createElement("span");
  label.textContent = "JioBot is thinking ";

  const dots = document.createElement("span");
  dots.classList.add("typing-dots");
  dots.innerHTML = "<span></span><span></span><span></span>";

  bubble.appendChild(label);
  bubble.appendChild(dots);
  row.appendChild(bubble);
  chatbox.appendChild(row);
  chatbox.scrollTop = chatbox.scrollHeight;
}

function removeTypingIndicator() {
  const row = document.getElementById("typing-row");
  if (row) row.remove();
}

async function sendMessage() {
  const question = userInput.value.trim();
  if (!question) return;

  const detailed = document.getElementById("detailedToggle")?.checked || false;
  const topKField = document.getElementById("topKInput");
  const top_k = topKField ? Number(topKField.value || 3) : 3;

  appendMessage(question, "user");
  userInput.value = "";
  autoResizeTextarea();

  sendBtn.disabled = true;
  appendTypingIndicator();

  const payload = { question, top_k, detailed };

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    removeTypingIndicator();
    sendBtn.disabled = false;

    if (data && data.answer) {
      appendMessage(data.answer, "bot", data.sources || []);
    } else {
      appendMessage("⚠️ No answer received from server.", "bot");
    }
  } catch (err) {
    console.error(err);
    removeTypingIndicator();
    sendBtn.disabled = false;
    appendMessage("❌ Error contacting server.", "bot");
  }
}

function autoResizeTextarea() {
  userInput.style.height = "auto";
  userInput.style.height = Math.min(userInput.scrollHeight, 80) + "px";
}

userInput.addEventListener("input", autoResizeTextarea);

userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

appendMessage(
  "👋 Hi! I’m your **Jio RAG Assistant**.\nAsk me anything about Jio apps, services, or products.",
  "bot"
);
