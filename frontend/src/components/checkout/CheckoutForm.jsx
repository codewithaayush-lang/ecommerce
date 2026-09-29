"use client";

import Link from "next/link";
import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { buttonStyles } from "@/components/ui/buttonStyles";
import { formatPrice } from "@/lib/format";
import { placeOrderAction } from "@/app/actions";

function PlaceOrderButton() {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className={`${buttonStyles({ size: "lg" })} w-full`}
    >
      {pending ? "Placing your order…" : "Place order"}
    </button>
  );
}

/**
 * Checkout form and order confirmation.
 *
 * Payment is intentionally not collected. On success the Server Action returns
 * the new order id, and the confirmation links to the order and the history.
 */
export default function CheckoutForm({ items }) {
  const [state, formAction] = useActionState(placeOrderAction, {
    error: null,
    success: false,
    orderId: null,
  });

  if (state?.success && state.orderId) {
    return (
      <div className="rounded-xl border border-brand-200 bg-brand-50/60 p-8">
        <p className="text-sm font-semibold tracking-wide text-brand-700 uppercase">
          Order placed
        </p>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-stone-900">
          Thank you for your order
        </h2>
        <p className="mt-2 text-stone-700">
          Your order number is{" "}
          <span className="font-semibold tabular-nums">#{state.orderId}</span>.
          Your cart is now empty.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href={`/orders/${state.orderId}`}
            className={buttonStyles({ size: "lg" })}
          >
            View this order
          </Link>
          <Link
            href="/orders"
            className={buttonStyles({ variant: "secondary", size: "lg" })}
          >
            Order history
          </Link>
          <Link
            href="/shop"
            className={buttonStyles({ variant: "secondary", size: "lg" })}
          >
            Continue shopping
          </Link>
        </div>
      </div>
    );
  }

  return (
    <form action={formAction} className="space-y-8">
      <section aria-labelledby="items-heading">
        <h2 id="items-heading" className="text-lg font-semibold text-stone-900">
          Items
        </h2>

        <ul className="mt-4 divide-y divide-stone-200 border-y border-stone-200">
          {items.map((item) => (
            <li key={item.id} className="flex justify-between gap-4 py-4 text-sm">
              <span className="min-w-0">
                <Link
                  href={`/shop/${item.slug}`}
                  className="font-medium text-stone-900 hover:text-brand-700"
                >
                  {item.name}
                </Link>
                <span className="mt-0.5 block text-xs text-stone-500 tabular-nums">
                  {formatPrice(item.unitPrice)} × {item.quantity}
                </span>
              </span>
              <span className="shrink-0 font-medium text-stone-900 tabular-nums">
                {formatPrice(item.lineTotal)}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="delivery-heading">
        <h2
          id="delivery-heading"
          className="text-lg font-semibold text-stone-900"
        >
          Delivery
        </h2>
        <p className="mt-2 text-sm text-stone-600">
          Shipping details are not collected yet. Your order will be recorded
          against your account.
        </p>
      </section>

      <section aria-labelledby="payment-heading">
        <h2
          id="payment-heading"
          className="text-lg font-semibold text-stone-900"
        >
          Payment
        </h2>
        <p className="mt-2 rounded-md border border-stone-200 bg-stone-50 px-3 py-2.5 text-sm text-stone-600">
          Payment is not collected in this step. Your order is recorded as
          pending and can be cancelled from your order history.
        </p>
      </section>

      {state?.error ? (
        <p
          role="alert"
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700"
        >
          {state.error}
        </p>
      ) : null}

      <div className="border-t border-stone-200 pt-6">
        <PlaceOrderButton />
      </div>
    </form>
  );
}
