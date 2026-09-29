import ProductCard from "@/components/products/ProductCard";
import EmptyState from "@/components/ui/EmptyState";

/**
 * Grid of products returned by the API.
 *
 * Takes a full page of results from the Django paginated response. An empty
 * result set renders a purpose-built empty state rather than an empty grid.
 */
export default function ProductGrid({ products, emptyTitle, emptyDescription }) {
  if (!products || products.length === 0) {
    return (
      <EmptyState title={emptyTitle} description={emptyDescription} />
    );
  }

  return (
    <ul className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </ul>
  );
}
