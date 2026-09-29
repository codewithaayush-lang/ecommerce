import Link from "next/link";
import Container from "@/components/ui/Container";
import { site } from "@/lib/site";

const stats = [
  { value: "Small batch", label: "Made in limited runs" },
  { value: "Built to last", label: "Designed for daily use" },
  { value: "Free returns", label: "Within 30 days" },
];

export default function Hero() {
  return (
    <section className="border-b border-stone-200 bg-gradient-to-b from-stone-50 to-white">
      <Container>
        <div className="grid gap-10 py-16 sm:py-24 lg:grid-cols-12 lg:items-center lg:gap-12">
          <div className="lg:col-span-7">
            <p className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-800">
              New season, small batches
            </p>

            <h1 className="mt-6 text-4xl font-semibold tracking-tight text-balance text-stone-900 sm:text-5xl lg:text-6xl">
              Durable goods, chosen carefully.
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-relaxed text-stone-600">
              {site.description}
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-3">
              <Link
                href="/shop"
                className="inline-flex items-center justify-center rounded-md bg-brand-700 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-800"
              >
                Shop all products
              </Link>
              <Link
                href="/categories"
                className="inline-flex items-center justify-center rounded-md border border-stone-300 bg-white px-6 py-3 text-sm font-semibold text-stone-700 transition-colors hover:bg-stone-50 hover:text-stone-900"
              >
                Browse categories
              </Link>
            </div>
          </div>

          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3 lg:col-span-5 lg:grid-cols-1">
            {stats.map((stat) => (
              <div
                key={stat.value}
                className="rounded-xl border border-stone-200 bg-white/70 p-5"
              >
                <dt className="text-sm font-semibold text-stone-900">
                  {stat.value}
                </dt>
                <dd className="mt-1 text-sm text-stone-500">{stat.label}</dd>
              </div>
            ))}
          </dl>
        </div>
      </Container>
    </section>
  );
}
