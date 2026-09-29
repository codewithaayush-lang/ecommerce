"use client";

import CatalogError from "@/components/ui/CatalogError";

/**
 * Error boundary for the /shop segment.
 *
 * Must be a Client Component: error boundaries are client-side. This wraps
 * `page.js` and `not-found.js` in the same segment.
 */
export default function ShopError({ error, retry }) {
  return (
    <CatalogError
      error={error}
      retry={retry}
      title="The catalog could not be loaded"
      description="We could not reach the store API. Check that the Django server is running, then try again."
    />
  );
}
