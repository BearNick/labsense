"use client";

import { useI18n } from "@/components/labsense/locale-provider";
import { localeLabels, SUPPORTED_LOCALES } from "@/lib/i18n";

export function LanguageToggle() {
  const { locale, setLocale, messages } = useI18n();

  return (
    <div
      className="inline-flex items-center gap-1 rounded-full border border-[var(--border)] bg-[var(--card)] p-1 text-xs"
      aria-label={messages.common.language}
    >
      {SUPPORTED_LOCALES.map((nextLocale) => (
        <button
          key={nextLocale}
          type="button"
          onClick={() => setLocale(nextLocale)}
          className={`rounded-full px-2.5 py-1 ${locale === nextLocale ? "bg-[var(--foreground)] text-[var(--background)]" : "text-[var(--muted-foreground)]"}`}
          aria-pressed={locale === nextLocale}
        >
          {localeLabels[nextLocale]}
        </button>
      ))}
    </div>
  );
}
