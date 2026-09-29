import Link from "next/link";
import { connection } from "next/server";
import Container from "@/components/ui/Container";
import CategoryCard from "@/components/categories/CategoryCard";
import { getCategories } from "@/lib/api";

/**
 * Category section on the home page, using the real categories from Django.
 *
 * Renders nothing at all when the store has no categories, so the home page
 * stays clean on an empty catalog.
 */
export default async function HomeCategories() {
  await connection();

  const categories = await getCategories();

  if (categories.length === 0) {
    return null;
  }

  return (
    <section
      aria-labelledby="home-categories-heading"
      className="border-t border-stone-200 bg-stone-50 py-16 sm:py-20"
    >
      <Container>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2
              id="home-categories-heading"
              className="text-2xl font-semibold tracking-tight text-stone-900 sm:text-3xl"
            >
              Shop by category
            </h2>
            <p className="mt-2 max-w-xl text-stone-600">
              Start with a category to narrow things down.
            </p>
          </div>

          <Link
            href="/categories"
            className="text-sm font-semibold text-brand-700 hover:text-brand-900"
          >
            All categories
          </Link>
        </div>

        <ul className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {categories.slice(0, 6).map((category) => (
            <CategoryCard key={category.id} category={category} />
          ))}
        </ul>
      </Container>
    </section>
  );
}
