/**
 * Visual placeholder for a product image.
 *
 * The catalog has no image field yet, so rather than implying a photo exists,
 * this renders a deliberate, neutral tile: a muted gradient chosen
 * deterministically from the product slug, with the product's initial as a
 * monogram. The same product always gets the same treatment, so grids look
 * varied but stable across renders.
 *
 * It is marked `aria-hidden` because the product name is always rendered
 * immediately next to it, so announcing the placeholder would be redundant.
 */

const TINTS = [
  "from-brand-100 via-stone-50 to-stone-100",
  "from-stone-200 via-stone-50 to-brand-50",
  "from-brand-50 via-white to-stone-200",
  "from-stone-100 via-brand-50 to-white",
];

/** Small deterministic string hash, so a slug always maps to the same tint. */
function hashString(value) {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) % 100000;
  }
  return hash;
}

export default function ProductImage({ product, className = "" }) {
  const seed = hashString(product.slug || product.name || "");
  const tint = TINTS[seed % TINTS.length];
  const monogram = (product.name || "?").trim().charAt(0).toUpperCase();

  return (
    <div
      aria-hidden="true"
      className={`relative flex aspect-[4/3] items-center justify-center overflow-hidden bg-gradient-to-br ${tint} ${className}`}
    >
      {/* Soft highlight so the tile does not read as a flat grey box. */}
      <div className="absolute inset-0 bg-[radial-gradient(120%_80%_at_50%_0%,rgba(255,255,255,0.65),transparent_60%)]" />
      <span className="relative font-serif text-5xl font-normal tracking-tight text-stone-400/90 select-none">
        {monogram}
      </span>
      <span className="absolute inset-0 rounded-t-xl ring-1 ring-stone-900/5 ring-inset" />
    </div>
  );
}
