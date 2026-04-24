import type { ReactNode } from "react";

import { buildPageMetadata } from "@/lib/seo";

export const metadata = buildPageMetadata({
  title: "Аккаунт | Labsense",
  path: "/account"
});

export default function AccountLayout({ children }: { children: ReactNode }) {
  return children;
}
