"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ACTIVE_CLASS =
  "rounded-md bg-brand-50 px-3 py-2 text-sm font-semibold text-brand-800";

/**
 * A navigation link that marks itself as the current page.
 *
 * This is the only new Client Component in the catalog shell. Active-page
 * state can only be known in the browser, so it needs `usePathname`. The
 * Navbar itself stays a Server Component and passes plain props down.
 *
 * `className` styles the inactive state; the active state always uses the
 * highlighted treatment so the current page is obvious.
 *
 * `exact` treats only the precise path as active, which suits "/" and avoids
 * highlighting Home while on /shop.
 */
export default function ActiveLink({
  href,
  children,
  exact = false,
  className = "",
}) {
  const pathname = usePathname();
  const isActive = exact ? pathname === href : pathname.startsWith(href);

  return (
    <Link
      href={href}
      aria-current={isActive ? "page" : undefined}
      className={isActive ? ACTIVE_CLASS : className}
    >
      {children}
    </Link>
  );
}
