import Link from "next/link";
import { buildShopHref } from "@/lib/shopHref";

/**
 * A category tile linking to the shop listing filtered by that category's slug.
 *
 * Shared by the home page and the /categories page. `href` is built by the
 * caller so the home page can link elsewhere if it needs to.
 */
export default function CategoryCard({ category, href }) {
  const target = href ?? buildShopHref({ category: category.slug });

  return (
    <li className="group relative flex h-full flex-col rounded-xl border border-stone-200 bg-white p-6 transition-shadow duration-150 hover:shadow-md">
      {/* Decorative leading mark, coloured deterministically per category. */}
      <span
        aria-hidden="true"
        className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-700/10 text-sm font-semibold text-brand-700"
      >
        {category.name.charAt(0).toUpperCase()}
      </span>

      <h3 className="mt-4 text-base font-semibold text-stone-900">
        <Link
          href={target}
          className="transition-colors after:absolute after:inset-0 group-hover:text-brand-700"
        >
          {category.name}
        </Link>
      </h3>

      {category.description ? (
        <p className="mt-2 line-clamp-3 text-sm text-stone-600">
          {category.description}
        </p>
      ) : (
        <p className="mt-2 text-sm text-stone-500">
          Browse everything in {category.name}.
        </p>
      )}

      <span
        aria-hidden="true"
        className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-brand-700 transition-transform group-hover:translate-x-0.5"
      >
        Shop {category.name}
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.75}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"
          />
        </svg>
      </span>
    </li>
  );
}
