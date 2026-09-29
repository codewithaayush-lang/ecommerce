import Link from "next/link";
import ActiveLink from "@/components/layout/ActiveLink";
import LogoutButton from "@/components/layout/LogoutButton";
import Container from "@/components/ui/Container";
import { mainNavLinks, site } from "@/lib/site";

const DESKTOP_LINK_CLASS =
  "rounded-md px-3 py-2 text-sm font-medium text-stone-600 transition-colors hover:bg-stone-100 hover:text-stone-900";

function SearchForm({ id }) {
  return (
    <form action="/shop" role="search" className="relative w-full">
      <label htmlFor={id} className="sr-only">
        Search products
      </label>
      <svg
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-stone-400"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.75}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
        />
      </svg>
      <input
        id={id}
        type="search"
        name="q"
        placeholder="Search products"
        autoComplete="off"
        className="w-full rounded-md border border-stone-300 bg-white py-2 pr-3 pl-9 text-sm text-stone-900 transition-colors placeholder:text-stone-400 hover:border-stone-400 focus:border-brand-600 focus:ring-2 focus:ring-brand-200 focus:outline-none"
      />
    </form>
  );
}

function AccountLinks({ user, itemCount }) {
  if (user) {
    return (
      <div className="flex items-center gap-1">
        <Link
          href="/orders"
          className={`${DESKTOP_LINK_CLASS} hidden sm:inline-flex`}
        >
          Orders
        </Link>
        <span
          className="hidden max-w-[10rem] truncate rounded-md bg-stone-100 px-3 py-2 text-sm font-medium text-stone-700 sm:inline"
          title={user.username}
        >
          {user.username}
        </span>
        <LogoutButton />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1">
      <ActiveLink href="/register" className={DESKTOP_LINK_CLASS}>
        Register
      </ActiveLink>
      <ActiveLink href="/login" className={DESKTOP_LINK_CLASS}>
        Login
      </ActiveLink>
    </div>
  );
}

/**
 * Mobile navigation. Uses native <details>/<summary> so the Navbar can stay a
 * Server Component.
 */
function MobileNav({ user, itemCount }) {
  return (
    <details className="group relative ml-auto md:hidden">
      <summary className="flex cursor-pointer list-none items-center rounded-md p-2 text-stone-700 transition-colors hover:bg-stone-100 [&::-webkit-details-marker]:hidden">
        <span className="sr-only">Toggle navigation menu</span>
        <svg
          className="h-6 w-6 group-open:hidden"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
          />
        </svg>
        <svg
          className="hidden h-6 w-6 group-open:block"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6 18 18 6M6 6l12 12"
          />
        </svg>
      </summary>

      <div className="absolute right-0 top-full z-50 mt-2 w-[min(20rem,calc(100vw-2rem))] rounded-xl border border-stone-200 bg-white p-3 shadow-lg">
        <nav aria-label="Mobile" className="flex flex-col gap-1">
          {mainNavLinks.map((link) => (
            <ActiveLink
              key={link.href}
              href={link.href}
              exact={link.exact}
              className={DESKTOP_LINK_CLASS}
            >
              {link.label}
            </ActiveLink>
          ))}
          <ActiveLink href="/cart" className={DESKTOP_LINK_CLASS}>
            Cart{itemCount > 0 ? ` (${itemCount})` : ""}
          </ActiveLink>
          {user ? (
            <>
              <ActiveLink href="/orders" className={DESKTOP_LINK_CLASS}>
                Orders
              </ActiveLink>
              <div className="mt-2 border-t border-stone-200 pt-2">
                <p className="px-3 py-1 text-xs text-stone-500">
                  Signed in as {user.username}
                </p>
                <LogoutButton className="w-full justify-center" />
              </div>
            </>
          ) : (
            <div className="mt-2 flex flex-col gap-1 border-t border-stone-200 pt-2">
              <ActiveLink href="/login" className={DESKTOP_LINK_CLASS}>
                Login
              </ActiveLink>
              <ActiveLink href="/register" className={DESKTOP_LINK_CLASS}>
                Register
              </ActiveLink>
            </div>
          )}
        </nav>

        <div className="mt-3 border-t border-stone-200 pt-3">
          <SearchForm id="mobile-search" />
        </div>
      </div>
    </details>
  );
}

/**
 * Site header.
 *
 * Reads the signed-in user on the server so the nav can render the correct
 * links. Only `ActiveLink` and `LogoutButton` are Client Components.
 */
export default async function Navbar({ user = null, itemCount = 0 }) {
  return (
    <header className="sticky top-0 z-40 border-b border-stone-200 bg-white/90 backdrop-blur">
      <Container>
        <div className="flex h-16 items-center gap-2">
          <Link
            href="/"
            className="flex shrink-0 items-center gap-2 rounded-md text-lg font-semibold tracking-tight text-brand-800"
          >
            <span
              aria-hidden="true"
              className="flex h-8 w-8 items-center justify-center rounded-md bg-brand-700 text-sm font-bold text-white"
            >
              {site.name.charAt(0)}
            </span>
            <span className="hidden sm:inline">{site.name}</span>
            <span className="sm:hidden">{site.name.split(" ")[0]}</span>
          </Link>

          <nav aria-label="Main" className="ml-2 hidden items-center gap-1 md:flex">
            {mainNavLinks.map((link) => (
              <ActiveLink
                key={link.href}
                href={link.href}
                exact={link.exact}
                className={DESKTOP_LINK_CLASS}
              >
                {link.label}
              </ActiveLink>
            ))}
          </nav>

          <div className="ml-auto hidden w-64 items-center gap-1 md:flex">
            <SearchForm id="desktop-search" />
          </div>

          <div className="ml-auto hidden items-center gap-1 md:flex">
            <ActiveLink href="/cart" className={DESKTOP_LINK_CLASS}>
              Cart
              {itemCount > 0 ? (
                <span className="ml-1.5 rounded-full bg-brand-700 px-1.5 py-0.5 text-xs font-semibold text-white tabular-nums">
                  {itemCount}
                </span>
              ) : null}
            </ActiveLink>
            <AccountLinks user={user} itemCount={itemCount} />
          </div>

          <MobileNav user={user} itemCount={itemCount} />
        </div>
      </Container>
    </header>
  );
}
