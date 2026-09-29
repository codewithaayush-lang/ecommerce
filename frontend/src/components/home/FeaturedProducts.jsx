import Link from "next/link";
import { connection } from "next/server";
import Container from "@/components/ui/Container";
import ProductImage from "@/components/products/ProductImage";
import EmptyState from "@/components/ui/EmptyState";
import { getProducts } from "@/lib/api";
import { formatPrice } from "@/lib/format";

/**
 * Latest products on the home page, straight from the Django API.
 *
 * `connection()` keeps this server-rendered per request rather than
 * prerendering the catalog into the page at build time.
 */
export default async function FeaturedProducts() {
  await connection();

  const { results } = await getProducts({ page: 1 });

  return (
    <section aria-labelledby="featured-heading" className="py-16 sm:py-20">
      <Container>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2
              id="featured-heading"
              className="text-2xl font-semibold tracking-tight text-stone-900 sm:text-3xl"
            >
              Latest products
            </h2>
            <p className="mt-2 max-w-xl text-stone-600">
              The most recent additions to the store.
            </p>
          </div>

          {results.length > 0 ? (
            <Link
              href="/shop"
              className="text-sm font-semibold text-brand-700 hover:text-brand-900"
            >
              View all products
            </Link>
          ) : null}
        </div>

        <div className="mt-8">
          {results.length === 0 ? (
            <EmptyState
              title="No products yet"
              description="New products will appear here as soon as they are added to the store."
              action={
                <Link
                  href="/shop"
                  className="text-sm font-semibold text-brand-700 underline underline-offset-4 hover:text-brand-900"
                >
                  Visit the shop
                </Link>
              }
            />
          ) : (
            <ul className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {results.slice(0, 8).map((product) => (
                <li
                  key={product.id}
                  className="group relative flex h-full flex-col overflow-hidden rounded-xl border border-stone-200 bg-white transition-shadow duration-150 hover:shadow-md"
                >
                  <ProductImage
                    product={product}
                    className={product.stock === 0 ? "opacity-60 saturate-50" : ""}
                  />

                  <div className="flex flex-1 flex-col p-4">
                    {product.category?.name ? (
                      <p className="text-xs font-medium tracking-wide text-stone-500 uppercase">
                        {product.category.name}
                      </p>
                    ) : null}

                    <h3 className="mt-1.5 text-sm font-semibold text-stone-900">
                      <Link
                        href={`/shop/${product.slug}`}
                        className="transition-colors after:absolute after:inset-0 group-hover:text-brand-700"
                      >
                        <span className="line-clamp-2">{product.name}</span>
                      </Link>
                    </h3>

                    <div className="mt-4 flex items-center justify-between gap-2 border-t border-stone-100 pt-3">
                      <p className="text-base font-semibold text-stone-900 tabular-nums">
                        {formatPrice(product.price)}
                      </p>
                      <span className="text-xs font-medium text-stone-500">
                        {product.stock > 0 ? "In stock" : "Out of stock"}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Container>
    </section>
  );
}
