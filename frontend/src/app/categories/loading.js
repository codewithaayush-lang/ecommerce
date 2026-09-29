import { SkeletonBlock } from "@/components/ui/Skeleton";

/**
 * Loading UI for the /categories segment.
 *
 * Safe to use here because this page never calls `notFound()`; a `loading.js`
 * above a page that does would turn its 404 into a streamed 200.
 */
export default function CategoriesLoading() {
  return (
    <div className="py-10 sm:py-12">
      <SkeletonBlock className="h-9 w-56" label="Loading categories" />
      <SkeletonBlock className="mt-4 h-5 w-80 max-w-full" />
      <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }, (_, index) => (
          <div
            key={index}
            className="h-44 animate-pulse rounded-xl border border-stone-200 bg-stone-100/70"
          />
        ))}
      </div>
      <span className="sr-only">Loading categories…</span>
    </div>
  );
}
