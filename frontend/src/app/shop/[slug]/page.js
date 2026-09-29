import Link from "next/link";
import { notFound } from "next/navigation";
import Container from "@/components/ui/Container";
import ProductImage from "@/components/products/ProductImage";
import { StockStatus } from "@/components/products/ProductCard";
import AddToCartForm from "@/components/cart/AddToCartForm";
import { buttonStyles } from "@/components/ui/buttonStyles";
import { getProduct } from "@/lib/api";
import { getCurrentUser } from "@/lib/serverApi";
import { formatPrice } from "@/lib/format";

/**
 * Product pages are looked up by slug at request time, so metadata is
 * generated per product.
 */
export async function generateMetadata({ params }) {
  const { slug } = await params;
  const product = await getProduct(slug);

  if (!product) {
    return { title: "Product not found" };
  }

  return {
    title: product.name,
    description: product.description.slice(0, 160),
  };
}

function formatDate(value) {
  return new Date(value).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default async function ProductDetailPage({ params }) {
  const { slug } = await params;
  const product = await getProduct(slug);

  // Covers both an unknown slug and a product that exists but is inactive,
  // because the API excludes inactive products from its public detail endpoint.
  // No loading.js sits above this route, so notFound() yields a real 404.
  if (!product) {
    notFound();
  }

  const soldOut = product.stock === 0;
  // Needed to decide between "add to cart" and "sign in to buy".
  const user = await getCurrentUser().catch(() => null);

  return (
    <Container>
      <div className="py-10 sm:py-12">
        <nav aria-label="Breadcrumb" className="text-sm text-stone-500">
          <Link href="/" className="hover:text-brand-700">
            Home
          </Link>
          <span className="mx-2" aria-hidden="true">
            /
          </span>
          <Link href="/shop" className="hover:text-brand-700">
            Shop
          </Link>
          {product.category ? (
            <>
              <span className="mx-2" aria-hidden="true">
                /
              </span>
              <Link
                href={`/shop?category=${product.category.slug}`}
                className="hover:text-brand-700"
              >
                {product.category.name}
              </Link>
            </>
          ) : null}
        </nav>

        <div className="mt-8 grid gap-10 lg:grid-cols-2 lg:gap-14">
          <div className="overflow-hidden rounded-xl border border-stone-200">
            <ProductImage
              product={product}
              className={soldOut ? "opacity-70 saturate-50" : ""}
            />
          </div>

          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-balance text-stone-900 sm:text-4xl">
              {product.name}
            </h1>

            {product.category ? (
              <p className="mt-3 text-sm">
                <Link
                  href={`/shop?category=${product.category.slug}`}
                  className="inline-flex items-center rounded-full border border-stone-300 px-3 py-1 font-medium text-stone-600 transition-colors hover:border-stone-400 hover:text-stone-900"
                >
                  {product.category.name}
                </Link>
              </p>
            ) : null}

            <p className="mt-6 text-3xl font-semibold text-stone-900 tabular-nums">
              {formatPrice(product.price)}
            </p>

            <div className="mt-4">
              <StockStatus
                stock={product.stock}
                isActive={product.is_active}
                size="md"
              />
            </div>

            {/*
              Stock and price are revalidated by Django when the item is added;
              the browser's values are never trusted.
            */}
            <div className="mt-8">
              <AddToCartForm
                productId={product.id}
                stock={product.stock}
                signedIn={Boolean(user)}
                disabled={soldOut}
              />
            </div>

            <dl className="mt-10 grid grid-cols-2 gap-x-6 gap-y-4 border-t border-stone-200 pt-6 text-sm">
              <div>
                <dt className="text-stone-500">Availability</dt>
                <dd className="mt-1 font-medium text-stone-900">
                  {product.is_active ? "Active" : "Inactive"}
                </dd>
              </div>
              <div>
                <dt className="text-stone-500">Units in stock</dt>
                <dd className="mt-1 font-medium text-stone-900 tabular-nums">
                  {product.stock}
                </dd>
              </div>
              <div>
                <dt className="text-stone-500">Added</dt>
                <dd className="mt-1 font-medium text-stone-900">
                  {formatDate(product.created_at)}
                </dd>
              </div>
              <div>
                <dt className="text-stone-500">Last updated</dt>
                <dd className="mt-1 font-medium text-stone-900">
                  {formatDate(product.updated_at)}
                </dd>
              </div>
            </dl>

            <div className="mt-10 border-t border-stone-200 pt-8">
              <h2 className="text-sm font-semibold tracking-wide text-stone-500 uppercase">
                Description
              </h2>
              <p className="mt-3 leading-relaxed whitespace-pre-line text-stone-700">
                {product.description}
              </p>
            </div>

            <div className="mt-10">
              <Link
                href={buildBackHref(product.category)}
                className={buttonStyles({ variant: "secondary" })}
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.75}
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18"
                  />
                </svg>
                Back to the catalog
              </Link>
            </div>
          </div>
        </div>
      </div>
    </Container>
  );
}

/** Returns to the category listing when the product has a category. */
function buildBackHref(category) {
  return category ? `/shop?category=${category.slug}` : "/shop";
}
