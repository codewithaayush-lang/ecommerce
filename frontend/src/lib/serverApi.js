/**
 * Authenticated client for the Django API.
 *
 * SERVER ONLY (it calls `cookies()`, so it cannot be imported by a Client
 * Component). All Next.js -> Django traffic goes through here, so the browser
 * never makes a cross-origin request to the API. That means:
 *
 *  - no CORS policy is required or configured
 *  - the session cookie stays HTTP-only and is never exposed to client JS
 *  - CSRF is still enforced: Django's SessionAuthentication checks the
 *    `X-CSRFToken` header on unsafe methods, populated from Django's own
 *    `csrftoken` cookie. Nothing here is csrf_exempt.
 */

import { cookies } from "next/headers";
import { ApiError } from "@/lib/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "");

/** Raised when Django reports the caller is not signed in. */
export class UnauthenticatedError extends Error {
  constructor() {
    super("Not authenticated");
    this.name = "UnauthenticatedError";
  }
}

function buildUrl(path, params) {
  if (!API_BASE_URL) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not set. Define it in .env.local (see .env.example).",
    );
  }
  const url = new URL(`${API_BASE_URL}${path}`);
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }
  return url;
}

/** Headers that forward the browser's session and CSRF token to Django. */
async function authHeaders() {
  const cookieStore = await cookies();
  const csrfToken = cookieStore.get("csrftoken")?.value;

  return {
    cookie: cookieStore.toString(),
    ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
  };
}

/** Raw fetch to Django, returning the untouched Response. */
async function rawRequest(path, { method = "GET", body, params } = {}) {
  return fetch(buildUrl(path, params), {
    method,
    headers: {
      ...(await authHeaders()),
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
}

async function toApiError(response, fallbackMessage) {
  const payload = await response.json().catch(() => null);
  const detail = payload?.detail;
  return new ApiError(
    typeof detail === "string" ? detail : fallbackMessage,
    response.status,
    payload,
  );
}

/**
 * Performs a request and returns parsed JSON, translating failures.
 *
 * `allow404` returns null instead of throwing, for endpoints where a missing
 * row is a normal outcome.
 */
async function request(path, options = {}) {
  const response = await rawRequest(path, options);

  if (options.allow404 && response.status === 404) return null;
  if (response.status === 401) throw new UnauthenticatedError();

  if (!response.ok) {
    throw await toApiError(
      response,
      `Request to ${path} failed with status ${response.status}`,
    );
  }

  if (response.status === 204) return null;
  return response.json();
}

/**
 * Copies Django's session and CSRF cookies onto the browser response.
 *
 * Only callable from a Server Action or Route Handler; Server Components
 * cannot set cookies.
 */
export async function forwardAuthCookies(response) {
  const setCookie = response.headers.getSetCookie?.() ?? [];
  const cookieStore = await cookies();

  for (const raw of setCookie) {
    const [pair, ...attributes] = raw.split(";");
    const index = pair.indexOf("=");
    if (index < 0) continue;

    const name = pair.slice(0, index).trim();
    const value = decodeURIComponent(pair.slice(index + 1).trim());
    const flags = attributes.map((a) => a.trim().toLowerCase());
    const has = (prefix) => flags.some((f) => f.startsWith(prefix));

    cookieStore.set(name, value, {
      path: "/",
      httpOnly: has("httponly"),
      secure: has("secure"),
      sameSite: has("samesite=none")
        ? "none"
        : has("samesite=lax")
          ? "lax"
          : "strict",
    });
  }
}

/**
 * Fetches Django's CSRF token cookie and stores it on the browser response.
 * Call before any write so Django accepts the unsafe request.
 */
export async function ensureCsrfCookie() {
  const response = await rawRequest("/auth/csrf/");
  if (!response.ok) {
    throw new Error("Could not obtain a CSRF token.");
  }
  await forwardAuthCookies(response);
}

// ---------------------------------------------------------------------------
// Auth endpoints
// ---------------------------------------------------------------------------

/** The signed-in user, or null when anonymous. */
export async function getCurrentUser() {
  try {
    return await request("/auth/me/");
  } catch (error) {
    if (error instanceof UnauthenticatedError) return null;
    throw error;
  }
}

export async function login({ username, password }) {
  const response = await rawRequest("/auth/login/", {
    method: "POST",
    body: { username, password },
  });
  if (!response.ok) {
    // Deliberately identical messaging for unknown user and wrong password.
    throw await toApiError(response, "Invalid username or password.");
  }
  await forwardAuthCookies(response);
  return response.json();
}

export async function register({ username, email, password }) {
  const response = await rawRequest("/auth/register/", {
    method: "POST",
    body: { username, email, password },
  });
  if (!response.ok) {
    throw await toApiError(response, "Registration failed.");
  }
  await forwardAuthCookies(response);
  return response.json();
}

export async function logout() {
  const response = await rawRequest("/auth/logout/", { method: "POST" });
  const cookieStore = await cookies();
  // Clear locally even if Django had already expired the session.
  cookieStore.delete("sessionid");
  cookieStore.delete("csrftoken");
  return response.ok;
}

// ---------------------------------------------------------------------------
// Cart endpoints
// ---------------------------------------------------------------------------

export async function getCart() {
  return request("/cart/");
}

export async function addCartItem({ productId, quantity = 1 }) {
  return request("/cart/items/", {
    method: "POST",
    body: { product_id: productId, quantity },
  });
}

export async function updateCartItem(itemId, { quantity }) {
  return request(`/cart/items/${itemId}/`, { method: "PATCH", body: { quantity } });
}

export async function removeCartItem(itemId) {
  return request(`/cart/items/${itemId}/`, { method: "DELETE" });
}

export async function clearCart() {
  return request("/cart/clear/", { method: "DELETE" });
}

// ---------------------------------------------------------------------------
// Order endpoints
// ---------------------------------------------------------------------------

export async function getOrders() {
  return request("/orders/");
}

export async function getOrder(id) {
  return request(`/orders/${id}/`, { allow404: true });
}

export async function placeOrder() {
  return request("/orders/", { method: "POST", body: {} });
}

export async function cancelOrder(id) {
  return request(`/orders/${id}/cancel/`, { method: "POST", body: {} });
}
