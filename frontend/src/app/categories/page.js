import { connection } from "next/server";
import Container from "@/components/ui/Container";
import CategoryCard from "@/components/categories/CategoryCard";
import EmptyState from "@/components/ui/EmptyState";
import { getCategories } from "@/lib/api";

export const metadata = {
  title: "Categories",
};

export default async function CategoriesPage() {
  // This page reads no request-time API, so it would otherwise be prerendered
  // at build time and bake in a stale catalog. `connection()` opts it into
  // per-request rendering. Pages that read `searchParams` or `params` (shop,
  // product detail) are dynamic automatically and do not need this.
  await connection();

  const categories = await getCategories();

  return (
    <Container>
      <div className="py-10 sm:py-12">
        <header className="max-w-2xl">
          <h1 className="text-3xl font-semibold tracking-tight text-stone-900 sm:text-4xl">
            Categories
          </h1>
          <p className="mt-3 text-stone-600">
            Every product belongs to one of these groups. Choose a category to
            see what is in it.
          </p>
        </header>

        <div className="mt-10">
          {categories.length === 0 ? (
            <EmptyState
              title="No categories yet"
              description="Categories will appear here once products are added to the store."
            />
          ) : (
            <>
              <p className="text-sm text-stone-600">
                <span className="font-semibold text-stone-900 tabular-nums">
                  {categories.length}
                </span>{" "}
                {categories.length === 1 ? "category" : "categories"}
              </p>

              {/*
                Per-category product counts are intentionally not shown: the
                categories endpoint does not include them, and deriving them
                would mean one API request per category. The backend could
                expose a product count on the category serializer to enable it.
              */}
              <ul className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {categories.map((category) => (
                  <CategoryCard key={category.id} category={category} />
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </Container>
  );
}
