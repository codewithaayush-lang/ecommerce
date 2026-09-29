import Link from "next/link";
import { buttonStyles } from "@/components/ui/buttonStyles";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-4 py-24 text-center">
      <p className="text-sm font-semibold tracking-wide text-brand-700 uppercase">
        404
      </p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-balance text-stone-900 sm:text-4xl">
        Page not found
      </h1>
      <p className="mt-4 text-stone-600">
        The page you were looking for does not exist, or it may have been
        removed.
      </p>

      <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
        <Link href="/" className={buttonStyles({ size: "lg" })}>
          Back to home
        </Link>
        <Link
          href="/shop"
          className={buttonStyles({ variant: "secondary", size: "lg" })}
        >
          Browse the shop
        </Link>
      </div>
    </div>
  );
}
