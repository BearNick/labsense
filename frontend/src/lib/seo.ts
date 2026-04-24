import type { Metadata } from "next";

const DEFAULT_SITE_URL = "https://labsense.app";
const DEFAULT_DESCRIPTION = "Быстрая и точная AI-интерпретация анализов крови. ОАК, биохимия, витамин D, CBC и международные лабораторные отчёты.";
const OG_IMAGE_PATH = "/og-image.svg";

export const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? DEFAULT_SITE_URL;
export const siteMetadataBase = new URL(siteUrl);

interface BuildPageMetadataOptions {
  title: string;
  path: string;
  description?: string;
}

export function buildPageMetadata({
  title,
  path,
  description = DEFAULT_DESCRIPTION
}: BuildPageMetadataOptions): Metadata {
  return {
    title,
    description,
    alternates: {
      canonical: path
    },
    openGraph: {
      title,
      description,
      type: "website",
      url: path,
      images: [
        {
          url: OG_IMAGE_PATH,
          width: 1200,
          height: 630,
          alt: "Labsense"
        }
      ]
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [OG_IMAGE_PATH]
    }
  };
}
