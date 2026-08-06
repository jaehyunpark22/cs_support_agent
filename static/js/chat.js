// URL의 ?user= 값으로 고객을 식별하고, /chat API를 호출해 대화를 주고받는다. 
// Enter로 전송, Shift+Enter로 줄바꿈을 구분해서 처리한다.

const params = new URLSearchParams(window.location.search);
const userId = Number(params.get("user"));

if (!userId || userId < 1 || userId > 5) {
  window.location.href = "/";
}

const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const customerTag = document.getElementById("customer-tag");
const sendButton = chatForm.querySelector("button");

customerTag.textContent = `손님 ${userId}번`;
chatInput.focus();

function appendMessage(text, className) {
  const el = document.createElement("div");
  el.className = `msg ${className}`;
  el.textContent = text;
  chatLog.appendChild(el);
  chatLog.scrollTop = chatLog.scrollHeight;
  return el;
}

function resetInputHeight() {
  chatInput.style.height = "auto";
}

async function loadHistory() {
  try {
    const response = await fetch(`/chat/history?user_id=${userId}`);
    if (!response.ok) return;
    const data = await response.json();
    data.messages.forEach((m) => {
      appendMessage(m.text, m.role === "customer" ? "msg--customer" : "msg--bot");
    });
  } catch (error) {
    // 기록을 못 불러와도 새 대화는 시작할 수 있어야 하므로 조용히 넘어간다
  }
}

loadHistory();

async function sendMessage(message) {
  appendMessage(message, "msg--customer");
  const pending = appendMessage("···", "msg--bot msg--pending");
  sendButton.disabled = true;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, message }),
    });

    if (!response.ok) {
      pending.remove();
      const errorText =
        response.status === 422
          ? "요청 형식에 문제가 있습니다. 새로고침 후 다시 시도해주세요."
          : "서버에서 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
      appendMessage(errorText, "msg--error");
      return;
    }

    const data = await response.json();
    pending.textContent = data.reply;
    pending.classList.remove("msg--pending");
  } catch (error) {
    pending.remove();
    appendMessage("서버에 연결할 수 없습니다. 네트워크 상태를 확인해주세요.", "msg--error");
  } finally {
    sendButton.disabled = false;
    chatInput.focus();
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  chatInput.value = "";
  resetInputHeight();
  sendMessage(message);
});

chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

chatInput.addEventListener("input", () => {
  chatInput.style.height = "auto";
  chatInput.style.height = `${chatInput.scrollHeight}px`;
});