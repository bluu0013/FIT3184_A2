// Lost pet search (rubric 3.2). Owner: Member C.
import { post } from "../api.js";
import { fileToBase64, h, toast } from "../dom.js";
import { renderGallery } from "../gallery.js";

export function mount(root) {
  const fileInput = h("input", { type: "file", id: "lp-file", accept: "image/*" });
  const tagsInput = h("input", { type: "text", id: "lp-tags", placeholder: "cat, ginger" });
  const daysInput = h("input", { type: "text", id: "lp-days", value: "30" });
  const detected = h("p", { class: "hint" });
  const gallery = h("div", { class: "gallery" });

  const search = async () => {
    const body = { days: Number(daysInput.value) || 30 };
    const tags = tagsInput.value.split(",").map((t) => t.trim()).filter(Boolean);
    if (tags.length) body.tags = tags;
    if (fileInput.files[0]) body.image_base64 = await fileToBase64(fileInput.files[0]);
    if (!body.tags && !body.image_base64) throw new Error("Add a photo or some tags");
    const data = await post("/search/lost-pet", body);
    detected.textContent = Object.keys(data.detected_tags || {}).length
      ? "Detected in your photo: " + Object.keys(data.detected_tags).join(", ") : "";
    renderGallery(gallery, data.results);
  };

  root.append(
    h("h2", {}, "Search for a lost pet"),
    h("p", { class: "hint" }, "Upload a photo and/or list tags such as the species, colour or breed. With tags only, the first one is the species."),
    h("label", { for: "lp-file" }, "Photo of your pet"),
    fileInput,
    h("label", { for: "lp-tags" }, "Tags (comma separated)"),
    tagsInput,
    h("label", { for: "lp-days" }, "Sightings from the last N days"),
    daysInput,
    h("div", { class: "row" }, h("button", { type: "button", onclick: async () => {
      try { await search(); } catch (err) { toast(err.message); }
    } }, "Search sightings")),
    detected,
    gallery,
  );
}
