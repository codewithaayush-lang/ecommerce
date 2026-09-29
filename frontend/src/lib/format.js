import { site } from "@/lib/site";

const priceFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: site.currency,
});

/**
 * Formats a price from the API.
 *
 * The API returns `price` as a string (DRF's default for `DecimalField`) so
 * that no precision is lost in transit; it is parsed to a number here only for
 * display.
 */
export function formatPrice(value) {
  const amount = Number.parseFloat(value);
  return Number.isNaN(amount) ? "" : priceFormatter.format(amount);
}
