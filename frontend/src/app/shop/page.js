import { Suspense } from "react";
import Link from "next/link";
import Container from "@/components/ui/Container";
import Pagination from "@/components/products/Pagination";
import ProductGrid from "@/components/products/ProductGrid";
import { FilterSkeleton, ProductGridSkeleton } from "@/components/ui/Skeleton";
import { ApiError, getCategories, getProducts } from "@/lib/api";
import { buildShopHref } from "@/lib/shopHref";

export const metadata = {
  title: "Shop",
};

/** Normalises `?page=` into a usable 1-based page number. */
function parsePage(value) {
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) || parsed < 1 ? 1 : parsed;
}

/**
 * Category filter. Rendered inside its own Suspense boundary so the filter
 * appears as soon as the (small) category request resolves, independently of
 * the product request.
 */
async function CategoryFilter({ activeCategory }) {
  const categories = await getCategories();

  if (categories.length === 0) {
    return null;
  }

  const base =
    "inline-flex items-center rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors";
  const inactiveClass = `${base} border-stone-300 bg-white text-stone-600 hover:border-stone-400 hover:text-stone-900`;
  const activeClass = `${base} border-brand-700 bg-brand-700 text-white`;

  return (
    <nav aria-label="Filter by category" className="flex flex-wrap gap-2">
      <Link
        href={buildShopHref({})}
        aria-current={activeCategory ? undefined : "page"}
        className={activeCategory ? inactiveClass : activeClass}
      >
        All products
      </Link>
      {categories.map((category) => {
        const isActive = category.slug === activeCategory;
        return (
          <Link
            key={category.id}
            href={buildShopHref({ category: category.slug })}
            aria-current={isActive ? "page" : undefined}
            className={isActive ? activeClass : inactiveClass}
          >
            {category.name}
          </Link>
        );
      })}
    </nav>
  );
}

/**
 * The current page of results: count, grid and pagination.
 *
 * Kept as a separate async component so it can sit inside a <Suspense>
 * boundary while the page heading and filter render immediately.
 */
async function ShopResults({ page, search, category }) {
  let products;

  try {
    products = await getProducts({ page, search, category });
  } catch (error) {
    // Django returns 404 when the requested page is past the end of the result
    // set. `notFound()` is deliberately not used here: it would be thrown from
    // inside the <Suspense> boundary below, which makes Next stream a 200
    // response with not-found content. A plain in-page message keeps the
    // status code honest and still offers a way forward.
    if (error instanceof ApiError && error.status === 404) {
      return (
        <div className="rounded-xl border border-dashed border-stone-300 bg-stone-50/60 px-6 py-14 text-center">
          <p className="text-sm font-medium text-stone-700">
            Page {page} is out of range for these results.
          </p>
          <Link
            href={buildShopHref({ page: 1, search, category })}
            className="mt-4 inline-block text-sm font-medium text-brand-700 underline underline-offset-4 hover:text-brand-900"
          >
            Go to the first page
          </Link>
        </div>
      );
    }
    throw error;
  }

  const hasFilters = Boolean(search || category);

  return (
    <>
      <p className="text-sm text-stone-600" aria-live="polite">
        {search ? (
          <>
            <span className="font-semibold text-stone-900 tabular-nums">
              {products.count}
            </span>{" "}
            {products.count === 1 ? "result" : "results"} for{" "}
            <span className="font-medium text-stone-900">“{search}”</span>
          </>
        ) : (
          <>
            <span className="font-semibold text-stone-900 tabular-nums">
              {products.count}
            </span>{" "}
            {products.count === 1 ? "product" : "products"}
            {category ? " in this category" : " in the catalog"}
          </>
        )}
      </p>

      <div className="mt-6">
        <ProductGrid
          products={products.results}
          emptyTitle={
            search
              ? `No products match “${search}”`
              : hasFilters
                ? "No products in this selection"
                : "No products yet"
          }
          emptyDescription={
            search
              ? "Try a different search term, or clear the filters to see the whole catalog."
              : hasFilters
                ? "This category has no active products right now."
                : "Products will appear here as soon as they are added to the store."
          }
        />
      </div>

      <Pagination
        count={products.count}
        page={page}
        search={search}
        category={category}
        hasNext={Boolean(products.next)}
        hasPrevious={Boolean(products.previous)}
      />
    </>
  );
}

export default async function ShopPage({ searchParams }) {
  const { page: rawPage, q, category } = await searchParams;
  const page = parsePage(rawPage);
  const search =
    typeof q === "string" && q.trim() ? q.trim().slice(0, 120) : undefined;
  const activeCategory =
    typeof category === "string" && category ? category : undefined;

  return (
    <Container>
      <div className="py-10 sm:py-12">
        <nav aria-label="Breadcrumb" className="text-sm text-stone-500">
          <Link href="/" className="hover:text-brand-700">
            Home
          </Link>
          <span className="mx-2" aria-hidden="true">
            /
          </span>
          <span className="text-stone-700">Shop</span>
        </nav>

        <header className="mt-4 max-w-2xl">
          <h1 className="text-3xl font-semibold tracking-tight text-stone-900 sm:text-4xl">
            {search ? "Search results" : "All products"}
          </h1>
          <p className="mt-3 text-stone-600">
            {search
              ? "Showing catalog matches for your search."
              : "Everything currently in the store. Filter by category or search to narrow it down."}
          </p>
        </header>

        {search ? (
          <p className="mt-6 inline-flex items-center gap-2 rounded-full border border-stone-200 bg-stone-50 py-1.5 pr-2 pl-4 text-sm text-stone-700">
            <span className="text-stone-500">Search:</span>
            <span className="font-medium text-stone-900">{search}</span>
            <Link
              href={buildShopHref({ category: activeCategory })}
              className="rounded-full p-1 text-stone-500 transition-colors hover:bg-stone-200 hover:text-stone-900"
            >
              <span className="sr-only">Clear search</span>
              <svg
                className="h-3.5 w-3.5"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18 18 6M6 6l12 12"
                />
              </svg>
            </Link>
          </p>
        ) : null}

        <div className="mt-8">
          <Suspense fallback={<FilterSkeleton />}>
            <CategoryFilter activeCategory={activeCategory} />
          </Suspense>
        </div>

        <div className="mt-8">
          <Suspense
            key={`${page}-${search ?? ""}-${activeCategory ?? ""}`}
            fallback={
              <div className="space-y-6">
                <div className="h-4 w-32 animate-pulse rounded bg-stone-200/70" />
                <ProductGridSkeleton />
              </div>
            }
          >
            <ShopResults
              page={page}
              search={search}
              category={activeCategory}
            />
          </Suspense>
        </div>
      </div>
    </Container>
  );
}
