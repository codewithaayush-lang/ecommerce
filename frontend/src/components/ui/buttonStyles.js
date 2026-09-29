/**
 * Shared class strings for buttons and button-like links.
 *
 * Kept as plain functions rather than a polymorphic component so that they can
 * be applied to a `next/link` (an anchor) or a real `<button>` without adding
 * an `as` prop or `use client` overhead.
 */

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50";

const VARIANTS = {
  primary: "bg-brand-700 text-white hover:bg-brand-800",
  secondary:
    "border border-stone-300 bg-white text-stone-700 hover:bg-stone-50 hover:text-stone-900",
  subtle: "text-brand-700 hover:text-brand-900",
  disabled: "border border-stone-200 bg-stone-100 text-stone-400",
};

const SIZES = {
  sm: "px-3 py-1.5",
  md: "px-4 py-2.5",
  lg: "px-6 py-3",
};

export function buttonStyles({ variant = "primary", size = "md" } = {}) {
  return [BASE, VARIANTS[variant] ?? VARIANTS.primary, SIZES[size] ?? SIZES.md]
    .filter(Boolean)
    .join(" ");
}

/** A neutral surface used for cards and panels. */
export const cardStyles =
  "rounded-xl border border-stone-200 bg-white transition-shadow duration-150";
