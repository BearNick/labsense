import type { ReactNode } from "react";

import { buildPageMetadata } from "@/lib/seo";

export const metadata = buildPageMetadata({
  title: "Результаты анализа крови | Labsense",
  path: "/results"
});

export default function ResultsLayout({ children }: { children: ReactNode }) {
  return children;
}
