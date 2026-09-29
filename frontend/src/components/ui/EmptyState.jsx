/**
 * Empty-state block for catalog sections.
 *
 * Used wherever the API legitimately returns nothing, so an empty catalog or a
 * search with no matches reads as an intentional state rather than a failure.
 */
export default function EmptyState({ title, description, action = null }) {
  return (
    <div className="rounded-xl border border-dashed border-stone-300 bg-stone-50/60 px-6 py-14 text-center">
      <p className="text-sm font-medium text-stone-700">{title}</p>
      {description ? (
        <p className="mx-auto mt-1 max-w-sm text-sm text-stone-500">
          {description}
        </p>
      ) : null}
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}
