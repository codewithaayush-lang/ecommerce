"use client";

import CatalogError from "@/components/ui/CatalogError";

/** Error boundary for the /categories segment. */
export default function CategoriesError({ error, retry }) {
  return (
    <CatalogError
      error={error}
      retry={retry}
      title="Categories could not be loaded"
      description="We could not reach the store API. Check that the Django server is running, then try again."
    />
  );
}
