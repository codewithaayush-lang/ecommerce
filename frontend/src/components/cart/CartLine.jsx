import Link from "next/link";
import ProductImage from "@/components/products/ProductImage";
import { updateCartItemAction, removeCartItemAction } from "@/app/actions";
import { formatPrice } from "@/lib/format";

/**
 * One cart line with quantity controls and a remove button.
 *
 * Each control is a small form posting to a Server Action, so the cart stays
 * server-rendered and Django remains the only source of truth. No client-side
 * cart state is kept.
 */
export default function CartLine({ item }) {
  const product = item.product;
  const maxQuantity = Math.max(item.max_quantity + item.quantity, item.quantity);

  return (
    <li className="flex flex-col gap-4 py-6 sm:flex-row sm:items-start sm:gap-6">
      <div className="w-full shrink-0 overflow-hidden rounded-lg border border-stone-200 sm:w-32">
        <Link
          href={`/shop/${product.slug}`}
          className="block focus-visible:outline-offset-[-2px]"
        >
          <ProductImage product={product} className="aspect-[4/3]" />
          <span className="sr-only">View {product.name}</span>
        </Link>
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-stone-900">
              <Link
                href={`/shop/${product.slug}`}
                className="hover:text-brand-700"
              >
                {product.name}
              </Link>
            </h3>
            {product.category?.name ? (
              <p className="mt-0.5 text-xs text-stone-500">
                {product.category.name}
              </p>
            ) : null}
          </div>

          <p className="text-sm font-semibold text-stone-900 tabular-nums">
            {formatPrice(item.line_total)}
          </p>
        </div>

        <p className="mt-1 text-xs text-stone-500 tabular-nums">
          {formatPrice(item.unit_price)} each
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <form
            action={updateCartItemAction}
            className="flex items-center gap-1.5"
          >
            <input type="hidden" name="item_id" value={item.id} />
            <label htmlFor={`qty-${item.id}`} className="sr-only">
              Quantity for {product.name}
            </label>
            <select
              id={`qty-${item.id}`}
              name="quantity"
              defaultValue={item.quantity}
              className="rounded-md border border-stone-300 bg-white py-1.5 pr-8 pl-3 text-sm text-stone-900 focus:border-brand-600 focus:ring-2 focus:ring-brand-200 focus:outline-none"
            >
              {Array.from({ length: Math.max(maxQuantity, item.quantity) }, (_, i) => (
                <option key={i + 1} value={i + 1}>
                  {i + 1}
                </option>
              ))}
            </select>
            <button
              type="submit"
              className="rounded-md border border-stone-300 px-3 py-1.5 text-sm font-medium text-stone-700 transition-colors hover:bg-stone-50"
            >
              Update
            </button>
          </form>

          <form action={removeCartItemAction}>
            <input type="hidden" name="item_id" value={item.id} />
            <button
              type="submit"
              className="text-sm font-medium text-stone-500 underline underline-offset-4 hover:text-stone-900"
            >
              Remove
            </button>
          </form>
        </div>

        {item.max_quantity === 0 ? (
          <p className="mt-2 text-xs text-amber-700">
            No more of this item is currently in stock.
          </p>
        ) : null}
      </div>
    </li>
  );
}
