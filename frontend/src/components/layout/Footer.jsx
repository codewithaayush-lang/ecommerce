import Link from "next/link";
import Container from "@/components/ui/Container";
import { mainNavLinks, site } from "@/lib/site";

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-auto border-t border-stone-200 bg-stone-50">
      <Container>
        <div className="grid gap-10 py-12 sm:grid-cols-2 lg:grid-cols-4">
          <div className="sm:col-span-2 lg:col-span-1">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-base font-semibold text-brand-800"
            >
              <span
                aria-hidden="true"
                className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-700 text-xs font-bold text-white"
              >
                {site.name.charAt(0)}
              </span>
              {site.name}
            </Link>
            <p className="mt-3 max-w-xs text-sm leading-relaxed text-stone-600">
              {site.tagline}
            </p>
          </div>

          <nav aria-label="Shop">
            <h2 className="text-sm font-semibold text-stone-900">Catalog</h2>
            <ul className="mt-4 space-y-3">
              {mainNavLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-stone-600 transition-colors hover:text-brand-700"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <nav aria-label="Account">
            <h2 className="text-sm font-semibold text-stone-900">Account</h2>
            <ul className="mt-4 space-y-3">
              <li>
                <Link
                  href="/cart"
                  className="text-sm text-stone-600 transition-colors hover:text-brand-700"
                >
                  Cart
                </Link>
              </li>
              <li>
                <Link
                  href="/login"
                  className="text-sm text-stone-600 transition-colors hover:text-brand-700"
                >
                  Login
                </Link>
              </li>
            </ul>
            <p className="mt-4 text-xs text-stone-400">
              Cart and accounts are not available yet.
            </p>
          </nav>
        </div>

        <div className="flex flex-col gap-2 border-t border-stone-200 py-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-stone-500">
            &copy; {year} {site.name}. All rights reserved.
          </p>
          <p className="text-xs text-stone-400">
            A portfolio project. Prices shown in {site.currency}.
          </p>
        </div>
      </Container>
    </footer>
  );
}
