"use client";

import Link from "next/link";
import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { buttonStyles } from "@/components/ui/buttonStyles";
import { addToCartAction } from "@/app/actions";

function AddButton({ disabled, label }) {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending || disabled}
      className={`${buttonStyles({ size: "lg" })} ${disabled ? buttonStyles({ variant: "disabled" }) : ""} w-full sm:w-auto`}
    >
      {pending ? "Adding…" : label}
    </button>
  );
}

/**
 * Add-to-cart control.
 *
 * The quantity is capped by what the server last reported as available, and
 * Django re-validates it on the write. The component holds no cart state: the
 * Server Action revalidates the page and the cart is re-read from Django.
 */
export default function AddToCartForm({ productId, stock, signedIn, disabled }) {
  const [state, formAction] = useActionState(addToCartAction, {
    error: null,
    success: null,
  });

  if (!signedIn) {
    return (
      <div>
        <Link href="/login" className={`${buttonStyles({ size: "lg" })}`}>
          Sign in to buy
        </Link>
        <p className="mt-3 text-xs text-stone-500">
          You need an account to keep a cart and place orders.
        </p>
      </div>
    );
  }

  const label = disabled ? "Out of stock" : "Add to cart";

  return (
    <form action={formAction} className="max-w-sm">
      <input type="hidden" name="product_id" value={productId} />

      <div className="flex items-end gap-3">
        <div>
          <label
            htmlFor={`qty-add-${productId}`}
            className="block text-sm font-medium text-stone-700"
          >
            Quantity
          </label>
          <input
            id={`qty-add-${productId}`}
            name="quantity"
            type="number"
            min={1}
            max={Math.max(stock, 1)}
            defaultValue={1}
            disabled={disabled}
            className="mt-1.5 w-24 rounded-md border border-stone-300 bg-white px-3 py-2.5 text-sm text-stone-900 focus:border-brand-600 focus:ring-2 focus:ring-brand-200 focus:outline-none disabled:bg-stone-100"
          />
        </div>

        <AddButton disabled={disabled} label={label} />
      </div>

      {state?.error ? (
        <p role="alert" className="mt-3 text-sm text-red-600">
          {state.error}
        </p>
      ) : null}

      {state?.success ? (
        <p className="mt-3 flex items-center gap-2 text-sm text-brand-700">
          {state.success}
          <Link
            href="/cart"
            className="font-medium underline underline-offset-4"
          >
            View cart
          </Link>
        </p>
      ) : null}
    </form>
  );
}
