// Cognito hosted UI sign-in with the authorization-code + PKCE flow. Owner: Member B. Cognito pool and client are Member A's.
// The UI guard here is for usability only; every API route is also protected by the JWT authorizer.
import { config } from "./config.js";

const TOKEN_KEY = "ecoguard.id_token";
const VERIFIER_KEY = "ecoguard.pkce_verifier";

function base64url(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes)))
    .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function pkcePair() {
  const verifier = base64url(crypto.getRandomValues(new Uint8Array(32)));
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
  return { verifier, challenge: base64url(digest) };
}

async function authorizeUrl(path) {
  const { verifier, challenge } = await pkcePair();
  sessionStorage.setItem(VERIFIER_KEY, verifier);
  const params = new URLSearchParams({
    client_id: config.clientId,
    response_type: "code",
    scope: "openid email profile",
    redirect_uri: config.redirectUri,
    code_challenge_method: "S256",
    code_challenge: challenge,
  });
  return `https://${config.cognitoDomain}/${path}?${params}`;
}

export async function signIn() {
  window.location.assign(await authorizeUrl("oauth2/authorize"));
}

export async function signUp() {
  window.location.assign(await authorizeUrl("signup"));
}

export function signOut() {
  sessionStorage.removeItem(TOKEN_KEY);
  const params = new URLSearchParams({ client_id: config.clientId, logout_uri: config.redirectUri });
  window.location.assign(`https://${config.cognitoDomain}/logout?${params}`);
}

/** Call once on load: swaps ?code=... for tokens and cleans the URL. */
export async function handleCallback() {
  const code = new URLSearchParams(window.location.search).get("code");
  if (!code) return;
  const verifier = sessionStorage.getItem(VERIFIER_KEY);
  window.history.replaceState({}, "", window.location.pathname);
  if (!verifier) return;
  const resp = await fetch(`https://${config.cognitoDomain}/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      client_id: config.clientId,
      code,
      redirect_uri: config.redirectUri,
      code_verifier: verifier,
    }),
  });
  sessionStorage.removeItem(VERIFIER_KEY);
  if (!resp.ok) throw new Error("Sign-in failed. Please try again.");
  sessionStorage.setItem(TOKEN_KEY, (await resp.json()).id_token);
}

function decode(token) {
  try {
    const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(decodeURIComponent(escape(atob(payload))));
  } catch {
    return null;
  }
}

/** The ID token if present and not expired, otherwise null. */
export function idToken() {
  const token = sessionStorage.getItem(TOKEN_KEY);
  const claims = token && decode(token);
  if (!claims || claims.exp * 1000 < Date.now()) return null;
  return token;
}

export function claims() {
  const token = idToken();
  return token ? decode(token) : null;
}
