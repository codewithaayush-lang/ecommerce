import Link from "next/link";
import { redirect } from "next/navigation";
import Container from "@/components/ui/Container";
import EmptyState from "@/components/ui/EmptyState";
import { buttonStyles } from "@/components/ui/buttonStyles";
import { getCurrentUser, getOrders } from "@/lib/serverApi";
import { formatPrice } from "@/lib/format";
import OrderStatusBadge from "@/components/orders/OrderStatusBadge";

export const metadata = {
  title: "Orders",
};

const STATUS_LABELS = {
  pending: "Pending",
  confirmed: "Confirmed",
  processing: "Processing",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

function formatDate(value) {
  return new Date(value).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default async function OrdersPage() {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  const orders = await getOrders();

  return (
    <Container>
      <div className="py-10 sm:py-12">
        <h1 className="text-3xl font-semibold tracking-tight text-stone-900 sm:text-4xl">
          Order history
        </h1>
        <p className="mt-2 text-stone-600">
          Every order you have placed with {user.username}.
        </p>

        <div className="mt-10">
          {!orders || orders.length === 0 ? (
            <EmptyState
              title="No orders yet"
              description="When you place an order it will appear here."
              action={
                <Link href="/shop" className={buttonStyles()}>
                  Start shopping
                </Link>
              }
            />
          ) : (
            <ul className="space-y-4">
              {orders.map((order) => (
                <li key={order.id}>
                  <Link
                    href={`/orders/${order.id}`}
                    className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-stone-200 bg-white p-5 transition-shadow hover:shadow-sm"
                  >
                    <div>
                      <p className="text-sm font-semibold text-stone-900">
                        Order #{order.id}
                      </p>
                      <p className="mt-1 text-xs text-stone-500">
                        {formatDate(order.created_at)} ·{" "}
                        {order.item_count}{" "}
                        {order.item_count === 1 ? "item" : "items"}
                      </p>
                    </div>

                    <div className="flex items-center gap-4">
                      <OrderStatusBadge status={order.status} />
                      <span className="text-sm font-semibold text-stone-900 tabular-nums">
                        {formatPrice(order.total)}
                      </span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        {orders && orders.length > 0 ? (
          <p className="mt-8 text-xs text-stone-400">
            Statuses: {Object.values(STATUS_LABELS).join(", ")}.
          </p>
        ) : null}
      </div>
    </Container>
  );
}
