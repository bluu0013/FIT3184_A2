// Query view (rubric 3.2): tags with counts, thumbnail URL, search by example file. Owner: Member C.
import { post } from "../api.js";
import { fileToBase64, h, parseTagCounts, toast } from "../dom.js";
import { renderGallery } from "../gallery.js";

export function mount(root) {
  const gallery = h("div", { class: "gallery" });
  const detected = h("p", { class: "hint" });

  const show = (data) => {
    detected.textContent = data.detected_tags
      ? "Detected in your file: " + (Object.keys(data.detected_tags).join(", ") || "nothing")
      : "";
    renderGallery(gallery, data.results || []);
  };
  const guard = (fn) => async () => {
    try { await fn(); } catch (err) { toast(err.message); }
  };

  const tagsInput = h("input", { type: "text", id: "q-tags", placeholder: "fox:2, feral pig:1" });
  const dateInput = h("input", { type: "text", id: "q-date", placeholder: "YYYY-MM-DD (optional)" });
  const thumbInput = h("input", { type: "text", id: "q-thumb", placeholder: "Paste a thumbnail URL" });
  const thumbOut = h("p", {});
  const fileInput = h("input", { type: "file", id: "q-file", accept: "image/*" });

  root.append(
    h("h2", {}, "Search"),
    h("label", { for: "q-tags" }, "By tags (all must match, with minimum counts)"),
    tagsInput,
    h("label", { for: "q-date" }, "Date"),
    dateInput,
    h("div", { class: "row" }, h("button", { type: "button", onclick: guard(async () => {
      const body = { tags: parseTagCounts(tagsInput.value) };
      if (dateInput.value.trim()) body.date = dateInput.value.trim();
      show(await post("/search/tags", body));
    }) }, "Search tags")),

    h("label", { for: "q-thumb" }, "Full-size image from a thumbnail URL"),
    thumbInput,
    h("div", { class: "row" }, h("button", { type: "button", class: "secondary", onclick: guard(async () => {
      const data = await post("/search/thumbnail", { thumbnail_url: thumbInput.value.trim() });
      thumbOut.replaceChildren(h("a", { href: data.url, target: "_blank", rel: "noopener" }, "Open full-size image"));
    }) }, "Find original")),
    thumbOut,

    h("label", { for: "q-file" }, "Find files that contain the same species as this image"),
    fileInput,
    h("p", { class: "hint" }, "Your image is analysed and discarded. It is not stored."),
    h("div", { class: "row" }, h("button", { type: "button", class: "secondary", onclick: guard(async () => {
      if (!fileInput.files[0]) throw new Error("Choose an image first");
      show(await post("/search/by-file", { image_base64: await fileToBase64(fileInput.files[0]) }));
    }) }, "Search by image")),

    detected,
    gallery,
  );
}
