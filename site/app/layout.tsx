import type { Metadata } from "next";
import { DM_Sans, Newsreader } from "next/font/google";
import "./globals.css";
import "./xray.css";
import { Analytics } from "@vercel/analytics/next";
import { copy } from "@/lib/copy";

const sans = DM_Sans({ subsets: ["latin"], variable: "--font-body", display: "swap" });
const serif = Newsreader({ subsets: ["latin"], style: ["normal", "italic"], axes: ["opsz"], variable: "--font-display", display: "swap" });
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
  return <html lang="en-CA" className={`${sans.variable} ${serif.variable}`}><body>{children}<div className="room-light" aria-hidden="true" /><Analytics /></body></html>;
}
