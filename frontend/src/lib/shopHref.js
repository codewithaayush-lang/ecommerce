/**
 * Builds a `/shop` URL while preserving the active search term and category
 * filter, so navigation never drops the user's query.
 */
export function buildShopHref({ page, search, category } = {}) {
  const params = new URLSearchParams();

  if (page && page > 1) {
    params.set("page", String(page));
  }
  if (search) {
    params.set("q", search);
  }
  if (category) {
    params.set("category", category);
  }

  const query = params.toString();
  return query ? `/shop?${query}` : "/shop";
}
