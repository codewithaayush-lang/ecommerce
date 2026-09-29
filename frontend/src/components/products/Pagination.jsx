import Link from "next/link";
import { PAGE_SIZE } from "@/lib/api";
import { buildShopHref } from "@/lib/shopHref";

/**
 * Page navigation for the shop listing.
 *
 * Previous/next availability comes from the API's `previous`/`next` fields, so
 * the control stays correct even if the page size changes on the backend.
 * Total pages are derived from the client-side `PAGE_SIZE` mirror.
 */
export default function Pagination({
  count,
  page,
  search,
  category,
  hasNext,
  hasPrevious,
}) {
  const totalPages = Math.ceil(count / PAGE_SIZE);

  if (totalPages <= 1) {
    return null;
  }

  const pageNumbers = [];
  const first = Math.max(1, Math.min(page - 2, totalPages - 4));
  const last = Math.min(totalPages, first + 4);
  for (let i = first; i <= last; i += 1) {
    pageNumbers.push(i);
  }

  const linkClass =
    "rounded-md border border-stone-300 px-3 py-2 text-sm text-stone-700 transition-colors hover:bg-stone-100";
  const activeClass =
    "rounded-md border border-brand-700 bg-brand-700 px-3 py-2 text-sm font-medium text-white";
  const disabledClass =
    "rounded-md border border-stone-200 px-3 py-2 text-sm text-stone-300";

  return (
    <nav
      aria-label="Pagination"
      className="mt-12 flex flex-wrap items-center justify-center gap-2"
    >
      {hasPrevious ? (
        <Link
          href={buildShopHref({ page: page - 1, search, category })}
          className={linkClass}
          rel="prev"
        >
          Previous
        </Link>
      ) : (
        <span className={disabledClass}>Previous</span>
      )}

      {pageNumbers.map((number) =>
        number === page ? (
          <span key={number} className={activeClass} aria-current="page">
            {number}
          </span>
        ) : (
          <Link
            key={number}
            href={buildShopHref({ page: number, search, category })}
            className={linkClass}
          >
            {number}
          </Link>
        ),
      )}

      {hasNext ? (
        <Link
          href={buildShopHref({ page: page + 1, search, category })}
          className={linkClass}
          rel="next"
        >
          Next
        </Link>
      ) : (
        <span className={disabledClass}>Next</span>
      )}
    </nav>
  );
}
