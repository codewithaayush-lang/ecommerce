export const site = {
  name: "Meridian Goods",
  tagline: "Considered goods for everyday use.",
  description:
    "Meridian Goods is a small online store for durable, thoughtfully made everyday items.",
  url: "https://example.com",
  // Display currency for prices. The API returns prices as decimal strings
  // without a currency, so formatting happens on the frontend.
  currency: "USD",
};

// `exact: true` means only that precise path counts as the current page,
// which is what Home needs so it is not highlighted while browsing /shop.
export const mainNavLinks = [
  { href: "/", label: "Home", exact: true },
  { href: "/shop", label: "Shop" },
  { href: "/categories", label: "Categories" },
];
