// Lex chatbot widget (rubric 3.3). Owner: Member C.
import { post } from "../api.js";
import { h } from "../dom.js";

const URL_RE = /(https?:\/\/[^\s]+)/g;

/** Append text to the log, turning URLs into links without using innerHTML. */
function addMessage(log, text, mine) {
  const el = h("div", { class: "msg" + (mine ? " me" : "") });
  text.split(URL_RE).forEach((part, i) => {
    el.append(i % 2 ? h("a", { href: part, target: "_blank", rel: "noopener" }, "open") : part);
  });
  log.append(el);
  log.scrollTop = log.scrollHeight;
}

export function mount(root) {
  const log = h("div", { class: "chat-log", "aria-live": "polite" });
  const input = h("input", { type: "text", id: "chat-text", placeholder: "Show me all photos of foxes" });
  let sessionId;

  const send = async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    addMessage(log, text, true);
    try {
      const out = await post("/chat", { text, session_id: sessionId });
      sessionId = out.session_id;
      (out.messages.length ? out.messages : ["(no reply)"]).forEach((m) => addMessage(log, m, false));
    } catch (err) {
      addMessage(log, "Error: " + err.message, false);
    }
  };
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });

  root.append(
    h("h2", {}, "Ask EcoGuard"),
    h("p", { class: "hint" }, 'Try "Show me all photos of foxes spotted yesterday" or "Help me find a lost ginger cat".'),
    log,
    h("label", { for: "chat-text" }, "Message"),
    input,
    h("div", { class: "row" }, h("button", { type: "button", onclick: send }, "Send")),
  );
}
