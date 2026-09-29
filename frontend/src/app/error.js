"use client";

import { useEffect } from "react";
import Link from "next/link";
import { buttonStyles } from "@/components/ui/buttonStyles";

/**
 * Root error boundary.
 *
 * Catches render failures anywhere in the app that no segment-level
 * `error.js` handled. Segment boundaries take precedence, so this is the
 * last-resort UI.
 */
export default function Error({ error, retry }) {
  useEffect(() => {
    // The server log is the source of truth; this keeps the failure visible in
    // the browser without leaking internals into the page.
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto max-w-xl px-4 py-24 text-center">
      <p className="text-sm font-semibold tracking-wide text-brand-700 uppercase">
        Something went wrong
      </p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-balance text-stone-900 sm:text-4xl">
        This page could not be loaded
      </h1>
      <p className="mt-4 text-stone-600">
        An unexpected error occurred. Trying again often resolves it.
      </p>

      <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
        <button
          type="button"
          onClick={() => retry()}
          className={buttonStyles({ size: "lg" })}
        >
          Try again
        </button>
        <Link
          href="/"
          className={buttonStyles({ variant: "secondary", size: "lg" })}
        >
          Back to home
        </Link>
      </div>
    </div>
  );
}
