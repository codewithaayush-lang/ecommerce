const STYLES = {
  pending: "bg-amber-50 text-amber-800 ring-amber-200",
  confirmed: "bg-brand-50 text-brand-800 ring-brand-200",
  processing: "bg-sky-50 text-sky-800 ring-sky-200",
  shipped: "bg-indigo-50 text-indigo-800 ring-indigo-200",
  delivered: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  cancelled: "bg-stone-100 text-stone-600 ring-stone-300",
};

const LABELS = {
  pending: "Pending",
  confirmed: "Confirmed",
  processing: "Processing",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

/** Status pill for an order. Unknown values fall back to a neutral style. */
export default function OrderStatusBadge({ status }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${
        STYLES[status] ?? STYLES.cancelled
      }`}
    >
      {LABELS[status] ?? status}
    </span>
  );
}
