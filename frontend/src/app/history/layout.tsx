import type { ReactNode } from "react";

import { buildPageMetadata } from "@/lib/seo";

export const metadata = buildPageMetadata({
  title: "История анализов | Labsense",
  path: "/history"
});

export default function HistoryLayout({ children }: { children: ReactNode }) {
  return children;
}
