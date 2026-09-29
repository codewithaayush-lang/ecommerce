"use client";

/**
 * Shared error UI for catalog sections.
 *
 * Must be a Client Component: it renders the retry control, and error
 * boundaries themselves are client-side. `retry` re-renders the segment, which
 * re-runs the server-side API request.
 */
export default function CatalogError({
  title = "Something went wrong",
  description = "We could not reach the store API. It may be starting up or temporarily unavailable.",
  error,
  retry,
}) {
  return (
    <div className="rounded-xl border border-stone-200 bg-stone-50/60 px-6 py-14 text-center">
      <p className="text-sm font-semibold text-stone-900">{title}</p>
      <p className="mx-auto mt-2 max-w-sm text-sm text-stone-600">
        {description}
      </p>

      {retry ? (
        <button
          type="button"
          onClick={() => retry()}
          className="mt-6 inline-flex items-center justify-center rounded-md bg-brand-700 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-800"
        >
          Try again
        </button>
      ) : null}

      {error?.message ? (
        <p className="mt-6 text-xs break-words text-stone-400">{error.message}</p>
      ) : null}
    </div>
  );
}
