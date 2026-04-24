import type { ReactNode } from "react";

import { buildPageMetadata } from "@/lib/seo";

export const metadata = buildPageMetadata({
  title: "Загрузка анализа крови | Labsense",
  path: "/upload"
});

export default function UploadLayout({ children }: { children: ReactNode }) {
  return children;
}
