import { Geist } from "next/font/google";
import "./globals.css";

import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { getCart, getCurrentUser } from "@/lib/serverApi";
import { site } from "@/lib/site";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata = {
  title: {
    default: site.name,
    template: `%s | ${site.name}`,
  },
  description: site.description,
};

export const viewport = {
  themeColor: "#ffffff",
};

export default async function RootLayout({ children }) {
  // The header shows who is signed in and how full the cart is. Both facts come
  // from Django on the server; nothing is cached in the browser.
  const user = await getCurrentUser().catch(() => null);

  // Only ask for the cart when there is a session, so anonymous page views do
  // not fire a request that is guaranteed to 401.
  const itemCount = user
    ? await getCart()
        .then((cart) => cart?.item_count ?? 0)
        .catch(() => 0)
    : 0;

  return (
    <html lang="en" className={`${geistSans.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <Navbar user={user} itemCount={itemCount} />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
