"use client";

import Link from "next/link";

import { useI18n } from "@/components/labsense/locale-provider";
import { cn } from "@/lib/utils";

type BrandMarkProps = {
  className?: string;
  iconClassName?: string;
  wordmarkClassName?: string;
  compact?: boolean;
};

export function LabsenseGlyph({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      aria-hidden="true"
      className={cn("h-9 w-9", className)}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="4" y="4" width="56" height="56" rx="18" fill="url(#labsense-bg)" />
      <path
        d="M23 18.5C17.8 22.9 15 29 15 32C15 35 17.8 41.1 23 45.5"
        stroke="url(#labsense-left)"
        strokeWidth="4.5"
        strokeLinecap="round"
      />
      <path
        d="M41 18.5C46.2 22.9 49 29 49 32C49 35 46.2 41.1 41 45.5"
        stroke="url(#labsense-right)"
        strokeWidth="4.5"
        strokeLinecap="round"
      />
      <rect x="29.5" y="17" width="5" height="24" rx="2.5" fill="#F6FBFA" />
      <circle cx="32" cy="46.5" r="4.5" fill="#9FE6D3" />
      <defs>
        <linearGradient id="labsense-bg" x1="10" y1="8" x2="56" y2="58" gradientUnits="userSpaceOnUse">
          <stop stopColor="#17242C" />
          <stop offset="1" stopColor="#0C1216" />
        </linearGradient>
        <linearGradient id="labsense-left" x1="15" y1="18.5" x2="28" y2="43" gradientUnits="userSpaceOnUse">
          <stop stopColor="#E8F7F2" />
          <stop offset="1" stopColor="#7FD8C3" />
        </linearGradient>
        <linearGradient id="labsense-right" x1="49" y1="18.5" x2="36" y2="43" gradientUnits="userSpaceOnUse">
          <stop stopColor="#E8F7F2" />
          <stop offset="1" stopColor="#7FD8C3" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export function LabsenseBrand({ className, iconClassName, wordmarkClassName, compact = false }: BrandMarkProps) {
  const { messages } = useI18n();

  return (
    <Link href="/" className={cn("inline-flex items-center gap-3", className)} aria-label="Labsense">
      <LabsenseGlyph className={iconClassName} />
      {!compact ? (
        <span className={cn("flex flex-col", wordmarkClassName)}>
          <span className="text-lg font-semibold tracking-[-0.03em] text-[var(--foreground)]">{messages.brand}</span>
          <span className="text-[11px] uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
            {messages.common.appTag}
          </span>
        </span>
      ) : null}
    </Link>
  );
}
