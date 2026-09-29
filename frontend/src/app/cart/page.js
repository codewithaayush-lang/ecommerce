import Link from "next/link";
import { redirect } from "next/navigation";
import Container from "@/components/ui/Container";
import EmptyState from "@/components/ui/EmptyState";
import CartLine from "@/components/cart/CartLine";
import { buttonStyles } from "@/components/ui/buttonStyles";
import { getCart, getCurrentUser } from "@/lib/serverApi";
import { formatPrice } from "@/lib/format";
import { clearCartAction } from "@/app/actions";

export const metadata = {
  title: "Cart",
};

export default async function CartPage() {
  const user = await getCurrentUser();
  if (!user) {
    // Send anonymous visitors to sign in, remembering where they were going.
    redirect("/login");
  }

  const cart = await getCart();
  const items = cart?.items ?? [];
  const isEmpty = items.length === 0;

  return (
    <Container>
      <div className="py-10 sm:py-12">
        <h1 className="text-3xl font-semibold tracking-tight text-stone-900 sm:text-4xl">
          Your cart
        </h1>
        <p className="mt-2 text-stone-600">
          {isEmpty
            ? "Nothing here yet."
            : `${cart.item_count} ${cart.item_count === 1 ? "item" : "items"} in your cart.`}
        </p>

        {isEmpty ? (
          <div className="mt-10">
            <EmptyState
              title="Your cart is empty"
              description="Browse the catalog and add something you like."
              action={
                <Link href="/shop" className={buttonStyles()}>
                  Browse products
                </Link>
              }
            />
          </div>
        ) : (
          <div className="mt-10 grid gap-10 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <ul className="divide-y divide-stone-200 border-y border-stone-200">
                {items.map((item) => (
                  <CartLine key={item.id} item={item} />
                ))}
              </ul>

              <form action={clearCartAction} className="mt-6">
                <button
                  type="submit"
                  className="text-sm font-medium text-stone-500 underline underline-offset-4 hover:text-stone-900"
                >
                  Clear cart
                </button>
              </form>
            </div>

            <aside className="lg:sticky lg:top-24 lg:self-start">
              <div className="rounded-xl border border-stone-200 bg-stone-50 p-6">
                <h2 className="text-sm font-semibold tracking-wide text-stone-500 uppercase">
                  Order summary
                </h2>

                <dl className="mt-5 space-y-3 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-stone-600">Subtotal</dt>
                    <dd className="font-medium text-stone-900 tabular-nums">
                      {formatPrice(cart.subtotal)}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-stone-600">Shipping</dt>
                    <dd className="text-stone-500">Calculated later</dd>
                  </div>
                </dl>

                <div className="mt-5 flex items-baseline justify-between border-t border-stone-200 pt-5">
                  <span className="text-sm font-semibold text-stone-900">Total</span>
                  <span className="text-xl font-semibold text-stone-900 tabular-nums">
                    {formatPrice(cart.total ?? cart.subtotal)}
                  </span>
                </div>

                <Link
                  href="/checkout"
                  className={`${buttonStyles({ size: "lg" })} mt-6 w-full`}
                >
                  Proceed to checkout
                </Link>

                <p className="mt-3 text-center text-xs text-stone-500">
                  No payment is collected yet.
                </p>
              </div>
            </aside>
          </div>
        )}
      </div>
    </Container>
  );
}
