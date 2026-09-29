/**
 * Shimmer-free loading placeholder.
 *
 * Deliberately simple: a muted block that pulses, with a screen-reader label
 * so the loading state is announced rather than being purely visual.
 */
export function SkeletonBlock({ className = "", label }) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-stone-200/70 ${className}`}
      role="status"
      aria-label={label}
    />
  );
}

/** Grid-shaped placeholder matching the product grid columns. */
export function ProductGridSkeleton({ count = 6 }) {
  return (
    <div
      className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
      role="status"
      aria-label="Loading products"
    >
      {Array.from({ length: count }, (_, index) => (
        <div
          key={index}
          className="flex flex-col overflow-hidden rounded-xl border border-stone-200 bg-white"
        >
          <div className="aspect-[4/3] animate-pulse bg-stone-200/70" />
          <div className="flex flex-col gap-3 p-5">
            <div className="h-3 w-1/3 animate-pulse rounded bg-stone-200/70" />
            <div className="h-4 w-3/4 animate-pulse rounded bg-stone-200/70" />
            <div className="mt-2 h-9 w-1/2 animate-pulse rounded bg-stone-200/70" />
          </div>
        </div>
      ))}
      <span className="sr-only">Loading products…</span>
    </div>
  );
}

/** Placeholder for the category filter row. */
export function FilterSkeleton() {
  return (
    <div
      className="flex flex-wrap gap-2"
      role="status"
      aria-label="Loading categories"
    >
      {Array.from({ length: 5 }, (_, index) => (
        <div
          key={index}
          className="h-8 w-24 animate-pulse rounded-full bg-stone-200/70"
        />
      ))}
      <span className="sr-only">Loading categories…</span>
    </div>
  );
}
