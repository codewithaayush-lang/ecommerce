import Link from "next/link";
import ProductImage from "@/components/products/ProductImage";
import { formatPrice } from "@/lib/format";

/** Availability pill. Out-of-stock products stay visible but clearly marked. */
export function StockStatus({ stock, isActive = true, size = "sm" }) {
  const base =
    "inline-flex items-center gap-1.5 rounded-full font-medium " +
    (size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm");

  if (!isActive) {
    return (
      <span className={`${base} bg-stone-200 text-stone-600`}>
        No longer available
      </span>
    );
  }

  if (stock > 0) {
    return (
      <span className={`${base} bg-brand-50 text-brand-700`}>
        <span className="h-1.5 w-1.5 rounded-full bg-brand-500" />
        In stock
        <span className="text-brand-600/70">({stock})</span>
      </span>
    );
  }

  return (
    <span className={`${base} bg-amber-50 text-amber-700`}>
      <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
      Out of stock
    </span>
  );
}

export default function ProductCard({ product }) {
  const soldOut = product.stock === 0;

  return (
    <li className="group relative flex h-full flex-col overflow-hidden rounded-xl border border-stone-200 bg-white transition-shadow duration-150 hover:shadow-md">
      <div className="relative">
        <ProductImage
          product={product}
          className={soldOut ? "opacity-60 saturate-50" : ""}
        />
        {soldOut ? (
          <span className="absolute left-3 top-3 rounded-full bg-white/90 px-2.5 py-1 text-xs font-medium text-stone-600 shadow-sm">
            Sold out
          </span>
        ) : null}
      </div>

      <div className="flex flex-1 flex-col p-5">
        {product.category?.name ? (
          <p className="text-xs font-medium tracking-wide text-stone-500 uppercase">
            {product.category.name}
          </p>
        ) : null}

        <h3 className="mt-1.5 text-base font-semibold text-stone-900">
          {/*
            A single link per card. The `after` overlay stretches its click
            target across the whole card, so the card is fully clickable while
            keyboard users still get exactly one tab stop and the product name
            is announced only once.
          */}
          <Link
            href={`/shop/${product.slug}`}
            className="transition-colors after:absolute after:inset-0 group-hover:text-brand-700"
          >
            {/* Long names wrap to two lines instead of stretching the card. */}
            <span className="line-clamp-2">{product.name}</span>
          </Link>
        </h3>

        <p className="mt-2 line-clamp-2 flex-1 text-sm text-stone-600">
          {product.description}
        </p>

        <div className="mt-5 flex items-end justify-between gap-3 border-t border-stone-100 pt-4">
          {/* tabular-nums keeps prices aligned across the grid regardless of
              how many digits they have. */}
          <p className="text-lg font-semibold text-stone-900 tabular-nums">
            {formatPrice(product.price)}
          </p>
          <StockStatus stock={product.stock} isActive={product.is_active} />
        </div>
      </div>
    </li>
  );
}
