// Small DOM helpers. Always build with textContent / append, never innerHTML with server data.

export function h(tag, props = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key.startsWith("on")) el.addEventListener(key.slice(2), value);
    else if (key === "class") el.className = value;
    else if (value !== false && value != null) el.setAttribute(key, value === true ? "" : value);
  }
  for (const kid of kids.flat()) if (kid != null) el.append(kid);
  return el;
}

export function toast(message) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.remove("show"), 3500);
}

/** "fox:2, feral pig:1, cat" -> {"fox": 2, "feral pig": 1, "cat": 1} */
export function parseTagCounts(text) {
  const out = {};
  for (const part of text.split(",")) {
    const [name, count] = part.split(":").map((s) => s.trim());
    if (!name) continue;
    const n = count ? Number(count) : 1;
    if (!Number.isInteger(n) || n < 1) throw new Error(`Bad count for "${name}"`);
    out[name.toLowerCase()] = n;
  }
  if (!Object.keys(out).length) throw new Error("Enter at least one tag, e.g. fox:2, cat");
  return out;
}

/** Read a File as base64 without the data: prefix. */
export function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.onerror = () => reject(new Error("Could not read the file"));
    reader.readAsDataURL(file);
  });
}

export async function sha256Hex(file) {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
