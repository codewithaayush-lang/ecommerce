import Link from "next/link";
import { buttonStyles } from "@/components/ui/buttonStyles";

export default function ProductNotFound() {
  return (
    <div className="mx-auto max-w-xl px-4 py-24 text-center">
      <p className="text-sm font-semibold tracking-wide text-brand-700 uppercase">
        Unavailable
      </p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-balance text-stone-900 sm:text-4xl">
        Product not found
      </h1>
      <p className="mt-4 text-stone-600">
        This product does not exist, or it is no longer available in the store.
      </p>

      <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
        <Link href="/shop" className={buttonStyles({ size: "lg" })}>
          Browse all products
        </Link>
        <Link
          href="/categories"
          className={buttonStyles({ variant: "secondary", size: "lg" })}
        >
          Shop by category
        </Link>
      </div>
    </div>
  );
}
