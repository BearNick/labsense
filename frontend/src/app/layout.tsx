import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/labsense/app-shell";
import { LocaleProvider } from "@/components/labsense/locale-provider";
import { siteMetadataBase, siteUrl } from "@/lib/seo";
import "./globals.css";

export const metadata: Metadata = {
  title: "Labsense — AI интерпретация анализов крови",
  description: "Быстрая и точная AI-интерпретация анализов крови. ОАК, биохимия, витамин D, CBC и международные лабораторные отчёты.",
  keywords: ["анализ крови", "расшифровка анализов", "CBC анализ", "биохимия крови", "AI медицина"],
  authors: [{ name: "Labsense" }],
  metadataBase: siteMetadataBase,
  alternates: {
    canonical: "/"
  },
  openGraph: {
    title: "Labsense — AI интерпретация анализов крови",
    description: "Быстрая и точная AI-интерпретация анализов крови. ОАК, биохимия, витамин D, CBC и международные лабораторные отчёты.",
    type: "website",
    url: "/",
    images: [
      {
        url: "/og-image.svg",
        width: 1200,
        height: 630,
        alt: "Labsense"
      }
    ]
  },
  twitter: {
    card: "summary_large_image",
    title: "Labsense — AI интерпретация анализов крови",
    description: "Быстрая и точная AI-интерпретация анализов крови. ОАК, биохимия, витамин D, CBC и международные лабораторные отчёты.",
    images: ["/og-image.svg"]
  },
  manifest: "/manifest.webmanifest",
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" }
    ],
    shortcut: "/icon.svg",
    apple: "/icon.svg"
  }
};

export const viewport: Viewport = {
  themeColor: "#10181e"
};

export default function RootLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: "Labsense",
    applicationCategory: "HealthApplication",
    description: "AI blood test interpretation",
    url: siteUrl,
    inLanguage: "en",
    operatingSystem: "Web"
  };

  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
      </head>
      <body>
        <LocaleProvider>
          <AppShell>{children}</AppShell>
        </LocaleProvider>
      </body>
    </html>
  );
}
