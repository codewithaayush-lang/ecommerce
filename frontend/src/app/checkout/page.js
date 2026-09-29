import Link from "next/link";
import { redirect } from "next/navigation";
import Container from "@/components/ui/Container";
import EmptyState from "@/components/ui/EmptyState";
import CheckoutForm from "@/components/checkout/CheckoutForm";
import { buttonStyles } from "@/components/ui/buttonStyles";
import { getCart, getCurrentUser } from "@/lib/serverApi";
import { formatPrice } from "@/lib/format";

export const metadata = {
  title: "Checkout",
};

export default async function CheckoutPage() {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  const cart = await getCart();
  const items = cart?.items ?? [];

  if (items.length === 0) {
    return (
      <Container>
        <div className="py-10 sm:py-12">
          <h1 className="text-3xl font-semibold tracking-tight text-stone-900">
            Checkout
          </h1>
          <div className="mt-10">
            <EmptyState
              title="There is nothing to check out"
              description="Your cart is empty. Add a product before placing an order."
              action={
                <Link href="/shop" className={buttonStyles()}>
                  Browse products
                </Link>
              }
            />
          </div>
        </div>
      </Container>
    );
  }

  return (
    <Container>
      <div className="py-10 sm:py-12">
        <nav aria-label="Breadcrumb" className="text-sm text-stone-500">
          <Link href="/cart" className="hover:text-brand-700">
            Cart
          </Link>
          <span className="mx-2" aria-hidden="true">
            /
          </span>
          <span className="text-stone-700">Checkout</span>
        </nav>

        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-stone-900 sm:text-4xl">
          Checkout
        </h1>
        <p className="mt-2 max-w-2xl text-stone-600">
          Review your order and place it. No payment is collected at this step.
        </p>

        <div className="mt-10 grid gap-10 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <CheckoutForm
              items={items.map((item) => ({
                id: item.id,
                name: item.product.name,
                slug: item.product.slug,
                quantity: item.quantity,
                lineTotal: item.line_total,
                unitPrice: item.unit_price,
              }))}
            />
          </div>

          <aside className="lg:sticky lg:top-24 lg:self-start">
            <div className="rounded-xl border border-stone-200 bg-stone-50 p-6">
              <h2 className="text-sm font-semibold tracking-wide text-stone-500 uppercase">
                Order summary
              </h2>

              <ul className="mt-5 space-y-3 text-sm">
                {items.map((item) => (
                  <li
                    key={item.id}
                    className="flex justify-between gap-3 text-stone-600"
                  >
                    <span className="min-w-0 truncate">
                      {item.product.name}{" "}
                      <span className="text-stone-400">×{item.quantity}</span>
                    </span>
                    <span className="shrink-0 tabular-nums">
                      {formatPrice(item.line_total)}
                    </span>
                  </li>
                ))}
              </ul>

              <dl className="mt-5 space-y-3 border-t border-stone-200 pt-5 text-sm">
                <div className="flex justify-between">
                  <dt className="text-stone-600">Subtotal</dt>
                  <dd className="font-medium text-stone-900 tabular-nums">
                    {formatPrice(cart.subtotal)}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-stone-600">Shipping</dt>
                  <dd className="text-stone-500">Not calculated</dd>
                </div>
              </dl>

              <div className="mt-5 flex items-baseline justify-between border-t border-stone-200 pt-5">
                <span className="text-sm font-semibold text-stone-900">Total</span>
                <span className="text-xl font-semibold text-stone-900 tabular-nums">
                  {formatPrice(cart.subtotal)}
                </span>
              </div>

              <p className="mt-4 rounded-md bg-white/70 px-3 py-2 text-xs text-stone-500">
                Totals are recalculated on the server when the order is placed.
                The browser never sets a price.
              </p>
            </div>
          </aside>
        </div>
      </div>
    </Container>
  );
}
