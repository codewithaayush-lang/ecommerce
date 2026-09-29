import Link from "next/link";

export default function PageStub({ title, description }) {
  return (
    <div className="py-20">
      <h1 className="text-3xl font-semibold tracking-tight text-stone-900">
        {title}
      </h1>
      <p className="mt-3 max-w-prose text-stone-600">{description}</p>
      <Link
        href="/"
        className="mt-6 inline-block text-sm font-medium text-brand-700 underline underline-offset-4 hover:text-brand-900"
      >
        Back to home
      </Link>
    </div>
  );
}
