import type { Metadata } from "next";
import { Source_Serif_4, Inter } from "next/font/google";
import "./globals.css";
import SWRegister from "@/components/SWRegister";

const sourceSerif = Source_Serif_4({
  variable: "--font-serif",
  subsets: ["latin"],
  weight: ["400", "600", "700"],
});

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: {
    default: "Grand Old Books",
    template: "%s | Grand Old Books",
  },
  description: "The greatest books you've never read",
  icons: { icon: "/favicon.png", apple: "/favicon.png" },
  manifest: "/manifest.json",
  metadataBase: new URL("https://grandoldbooks.com"),
  robots: { index: true, follow: true },
  keywords: ["classic literature", "free books online", "Indian literature", "world literature", "free ebooks", "translated books", "ancient texts"],
  alternates: {
    canonical: "/",
    types: { "application/rss+xml": "/feed.xml" },
  },
  openGraph: {
    type: "website",
    siteName: "Grand Old Books",
    title: "Grand Old Books",
    description: "The greatest books you've never read",
    images: [{ url: "/og.png", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Grand Old Books",
    description: "The greatest books you've never read",
    images: ["/og.png"],
  },
};

const GA_ID = process.env.NEXT_PUBLIC_GA_ID || "G-K47C7Q43HF";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <link rel="preconnect" href="https://storage.googleapis.com" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "WebSite",
              name: "Grand Old Books",
              url: "https://grandoldbooks.com",
              potentialAction: {
                "@type": "SearchAction",
                target: "https://grandoldbooks.com/?q={search_term_string}",
                "query-input": "required name=search_term_string",
              },
            }),
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Organization",
              name: "Grand Old Books",
              url: "https://grandoldbooks.com",
              logo: "https://grandoldbooks.com/favicon.png",
            }),
          }}
        />
        <link rel="prefetch" href="/data/search/index.json" as="fetch" crossOrigin="anonymous" />
        {GA_ID && (
          <>
            <script async src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`} />
            <script
              dangerouslySetInnerHTML={{
                __html: `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${GA_ID}');`,
              }}
            />
          </>
        )}
      </head>
      <body
        className={`${inter.variable} ${sourceSerif.variable} font-sans antialiased`}
        suppressHydrationWarning
      >
        <SWRegister />
        {children}
      </body>
    </html>
  );
}
