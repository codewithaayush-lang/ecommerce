"use client";

import { useFormStatus } from "react-dom";
import { logoutAction } from "@/app/actions";

function Button({ className = "" }) {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className={
        className ||
        "rounded-md px-3 py-2 text-sm font-medium text-stone-600 transition-colors hover:bg-stone-100 hover:text-stone-900 disabled:opacity-60"
      }
    >
      {pending ? "Signing out…" : "Sign out"}
    </button>
  );
}

/**
 * Logout control. A form posting to a Server Action so the session is ended on
 * the Django side, not merely in the browser.
 */
export default function LogoutButton({ className }) {
  return (
    <form action={logoutAction}>
      <Button className={className} />
    </form>
  );
}
