/**
 * Typed client for the Django catalog API.
 *
 * The Django backend is the single source of truth for catalog data. Nothing
 * in this file caches or stores product data locally; every function performs a
 * fresh request.
 *
 * All functions are safe to call from React Server Components: they use the
 * global `fetch` and take no browser-only APIs.
 */

const RAW_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

/**
 * Page size requested from the API.
 *
 * The Django API paginates with `PAGE_SIZE` (see `config/settings.py`). That
 * value is not included in the response body, so the client mirrors it here.
 * Keep the two in sync; the `next`/`previous` links from the API are used for
 * navigation, so a mismatch degrades gracefully rather than breaking paging.
 */
export const PAGE_SIZE = 12;

export class ApiError extends Error {
  /**
   * @param {string} message
   * @param {number} status  HTTP status returned by Django.
   * @param {object} [payload] Full parsed error body, used to surface
   *   per-field validation messages from DRF serializers.
   */
  constructor(message, status, payload = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }

  /**
   * Flattens a DRF error body into `{ field: "message" }`.
   *
   * DRF returns either `{field: [msgs]}` or a plain `{detail: "..."}`. Anything
   * unrecognised is ignored so callers always get a string per field.
   */
  get fieldErrors() {
    const body = this.payload;
    if (!body || typeof body !== "object") return {};

    const fields = {};
    for (const [key, value] of Object.entries(body)) {
      if (key === "detail" || key === "non_field_errors") continue;
      if (Array.isArray(value)) {
        fields[key] = value.map(String).join(" ");
      } else if (typeof value === "string") {
        fields[key] = value;
      }
    }
    return fields;
  }
}

function getBaseUrl() {
  const base = RAW_BASE_URL?.replace(/\/+$/, "");
  if (!base) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not set. Define it in .env.local (see .env.example).",
    );
  }
  return base;
}

function buildUrl(path, params) {
  // `path` must start with a slash; the base has no trailing slash, so simple
  // concatenation preserves the `/api` prefix.
  const url = new URL(`${getBaseUrl()}${path}`);

  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }

  return url;
}

/**
 * Performs a GET request and returns parsed JSON.
 *
 * `cache: "no-store"` is explicit: the catalog changes over time and this is a
 * development build, so serving a stale product list or price would be
 * confusing. Callers opt into caching later if they want it.
 *
 * Throws `ApiError` for any non-2xx response.
 */
async function apiFetch(path, { params } = {}) {
  const url = buildUrl(path, params);
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) {
    throw new ApiError(
      `GET ${url.pathname} failed with status ${response.status}`,
      response.status,
    );
  }

  return response.json();
}

/**
 * Returns a page of active products.
 *
 * @param {object} [options]
 * @param {number|string} [options.page]    1-based page number.
 * @param {string} [options.search]          Matches product name or description.
 * @param {string} [options.category]        Category slug to filter by.
 * @returns {Promise<{count: number, next: string|null, previous: string|null, results: object[]}>}
 */
export async function getProducts({ page, search, category } = {}) {
  const data = await apiFetch("/products/", {
    params: { page, search, category },
  });

  return {
    count: data.count,
    next: data.next,
    previous: data.previous,
    results: data.results,
  };
}

/**
 * Returns one active product, or `null` when it does not exist or is inactive.
 *
 * A missing product is not an error here: callers decide how to present it,
 * usually with `notFound()`.
 */
export async function getProduct(slug) {
  try {
    return await apiFetch(`/products/${encodeURIComponent(slug)}/`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

/**
 * Returns every category. The API returns a plain array for this endpoint.
 */
export async function getCategories() {
  return apiFetch("/categories/");
}

/**
 * Returns one category with its active products, or `null` when missing.
 */
export async function getCategory(slug) {
  try {
    return await apiFetch(`/categories/${encodeURIComponent(slug)}/`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}
