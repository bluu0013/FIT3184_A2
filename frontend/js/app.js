// App shell: sign-in gate and tab navigation. Owner: Member A.
import * as auth from "./auth.js";
import { config } from "./config.js";
import { toast } from "./dom.js";
import { mount as mountChat } from "./views/chat.js";
import { mount as mountLost } from "./views/lost.js";
import { mount as mountSearch } from "./views/search.js";
import { mount as mountTags } from "./views/tags.js";
import { mount as mountUpload } from "./views/upload.js";

const VIEWS = { upload: mountUpload, search: mountSearch, lost: mountLost, tags: mountTags, chat: mountChat };
const $ = (id) => document.getElementById(id);

function showTab(name) {
  document.querySelectorAll("#tabs button").forEach((b) => {
    b.setAttribute("aria-selected", String(b.dataset.view === name));
  });
  for (const view of Object.keys(VIEWS)) $("view-" + view).hidden = view !== name;
}

async function main() {
  if (config.apiUrl === "REPLACE_ME") {
    toast("Fill in frontend/js/config.js from the stack outputs first.");
  }
  try {
    await auth.handleCallback();
  } catch (err) {
    toast(err.message);
  }

  $("signin").addEventListener("click", () => auth.signIn());
  $("signup").addEventListener("click", () => auth.signUp());
  $("signout").addEventListener("click", () => auth.signOut());

  const claims = auth.claims();
  if (!claims) {
    $("landing").hidden = false;
    return;
  }

  $("user-name").textContent = [claims.given_name, claims.family_name].filter(Boolean).join(" ") || claims.email || "";
  $("signout").hidden = false;
  $("app").hidden = false;
  for (const [name, mount] of Object.entries(VIEWS)) mount($("view-" + name));
  $("tabs").addEventListener("click", (e) => {
    const view = e.target.dataset && e.target.dataset.view;
    if (view) showTab(view);
  });
  showTab("upload");
}

main();
