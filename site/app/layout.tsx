import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";
import "./xray.css";
import { Analytics } from "@vercel/analytics/next";
import { copy } from "@/lib/copy";

const sans = DM_Sans({ subsets: ["latin"], variable: "--font-body", display: "swap" });
// Display type is set at 400, so Newsreader ships as Google's weight-400 instance (latin, optical-size axis kept):
// 120 KB instead of 279 KB for the full weight range. next/font/google can't pin a weight while keeping an axis.
// Source: fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400
const newsreader = localFont({
  src: [{ path: "./fonts/newsreader-400.woff2", weight: "400", style: "normal" }, { path: "./fonts/newsreader-400-italic.woff2", weight: "400", style: "italic" }],
  variable: "--font-display",
  display: "swap",
  // Keeps the fallback metrics next/font/google used (app/globals.css).
  adjustFontFallback: false,
  fallback: ["Newsreader Fallback"],
});
// Metadata is invisible on the page; it drives SERPs, tabs, and share cards. Guides override their own per page.
export const metadata: Metadata = {
  metadataBase: new URL("https://ophi.app"),
  title: copy.title,
  description: copy.description,
  keywords: [...copy.keywords],
  applicationName: copy.name,
  robots: { index: true, follow: true },
  alternates: { canonical: "/" },
  openGraph: {
    title: copy.title,
    description: copy.description,
    type: "website",
    locale: "en_CA",
    url: "/",
    siteName: copy.name,
    images: [{ url: "/opengraph-image.png", width: 1200, height: 630, alt: copy.name }],
  },
  twitter: {
    card: "summary_large_image",
    title: copy.title,
    description: copy.description,
    images: ["/opengraph-image.png"],
  },
};
export default function RootLayout({ children }: LayoutProps<"/">) {
  return <html lang="en-CA" className={`${sans.variable} ${newsreader.variable}`}><body>{children}<div className="room-light" aria-hidden="true" /><Analytics /></body></html>;
}
