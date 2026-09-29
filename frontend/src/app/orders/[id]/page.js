import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import Container from "@/components/ui/Container";
import OrderStatusBadge from "@/components/orders/OrderStatusBadge";
import { buttonStyles } from "@/components/ui/buttonStyles";
import { getCurrentUser, getOrder } from "@/lib/serverApi";
import { formatPrice } from "@/lib/format";
import { cancelOrderAction } from "@/app/actions";

export async function generateMetadata({ params }) {
  const { id } = await params;
  return { title: `Order #${id}` };
}

function formatDateTime(value) {
  return new Date(value).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function OrderDetailPage({ params }) {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  const { id } = await params;
  const order = await getOrder(id);

  // Django scopes orders to the requesting user, so another user's order is a
  // 404 here exactly as a missing one is.
  if (!order) {
    notFound();
  }

  return (
    <Container>
      <div className="py-10 sm:py-12">
        <nav aria-label="Breadcrumb" className="text-sm text-stone-500">
          <Link href="/orders" className="hover:text-brand-700">
            Orders
          </Link>
          <span className="mx-2" aria-hidden="true">
            /
          </span>
          <span className="text-stone-700">Order #{order.id}</span>
        </nav>

        <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-stone-900 sm:text-4xl">
              Order #{order.id}
            </h1>
            <p className="mt-2 text-sm text-stone-600">
              Placed {formatDateTime(order.created_at)}
            </p>
          </div>
          <OrderStatusBadge status={order.status} />
        </div>

        <div className="mt-10 grid gap-10 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <h2 className="text-sm font-semibold tracking-wide text-stone-500 uppercase">
              Items
            </h2>

            <ul className="mt-4 divide-y divide-stone-200 border-y border-stone-200">
              {order.items.map((item) => (
                <li
                  key={item.id}
                  className="flex flex-wrap justify-between gap-4 py-4"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-stone-900">
                      {/* Snapshot name, not the current product name. */}
                      {item.product_name}
                    </p>
                    <p className="mt-0.5 text-xs text-stone-500 tabular-nums">
                      {formatPrice(item.unit_price)} × {item.quantity}
                    </p>
                  </div>
                  <p className="text-sm font-medium text-stone-900 tabular-nums">
                    {formatPrice(item.line_total)}
                  </p>
                </li>
              ))}
            </ul>
          </div>

          <aside className="lg:sticky lg:top-24 lg:self-start">
            <div className="rounded-xl border border-stone-200 bg-stone-50 p-6">
              <h2 className="text-sm font-semibold tracking-wide text-stone-500 uppercase">
                Summary
              </h2>

              <dl className="mt-5 space-y-3 text-sm">
                <div className="flex justify-between">
                  <dt className="text-stone-600">Subtotal</dt>
                  <dd className="font-medium text-stone-900 tabular-nums">
                    {formatPrice(order.subtotal)}
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
                  {formatPrice(order.total)}
                </span>
              </div>

              {order.can_cancel ? (
                <form action={cancelOrderAction} className="mt-6">
                  <input type="hidden" name="order_id" value={order.id} />
                  <button
                    type="submit"
                    className={`${buttonStyles({ variant: "secondary" })} w-full`}
                  >
                    Cancel this order
                  </button>
                </form>
              ) : null}

              <p className="mt-4 text-xs text-stone-500">
                Cancelling returns the reserved items to stock.
              </p>
            </div>
          </aside>
        </div>
      </div>
    </Container>
  );
}
