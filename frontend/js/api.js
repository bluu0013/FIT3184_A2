// Thin wrapper over the REST API: adds the Cognito token and unwraps errors.
import { config } from "./config.js";
import { idToken, signIn } from "./auth.js";

export async function post(path, body) {
  const token = idToken();
  if (!token) {
    await signIn();
    throw new Error("Your session expired. Redirecting to sign in.");
  }
  const resp = await fetch(config.apiUrl + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  const data = await resp.json().catch(() => ({}));
  if (resp.status === 401) {
    await signIn();
    throw new Error("Your session expired. Redirecting to sign in.");
  }
  if (!resp.ok) throw new Error(data.error || data.message || `Request failed (${resp.status})`);
  return data;
}
