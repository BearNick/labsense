"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

import { useI18n } from "@/components/labsense/locale-provider";
import { readAnalysisSessionLocale } from "@/lib/analysis-session";
import { getMessages, localeLabels, SUPPORTED_LOCALES, type Locale } from "@/lib/i18n";

export function LanguageToggle() {
  const { locale, setLocale, messages } = useI18n();
  const pathname = usePathname();
  const [reportLanguage, setReportLanguage] = useState<Locale | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    if (pathname === "/results") {
      setReportLanguage(readAnalysisSessionLocale());
      return;
    }

    setReportLanguage(null);
    setToastMessage(null);
  }, [pathname]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  function handleLocaleChange(nextLocale: Locale) {
    if (nextLocale === locale) {
      return;
    }

    setLocale(nextLocale);

    if (pathname !== "/results" || !reportLanguage || nextLocale === reportLanguage) {
      setToastMessage(null);
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current);
      }
      return;
    }

    setToastMessage(getMessages(nextLocale).results.languageMismatchToast);
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = window.setTimeout(() => {
      setToastMessage(null);
      timeoutRef.current = null;
    }, 3000);
  }

  return (
    <div className="relative">
      <div
        className="inline-flex items-center gap-1 rounded-full border border-[var(--border)] bg-[var(--card)] p-1 text-xs"
        aria-label={messages.common.language}
      >
        {SUPPORTED_LOCALES.map((nextLocale) => (
          <button
            key={nextLocale}
            type="button"
            onClick={() => handleLocaleChange(nextLocale)}
            className={`rounded-full px-2.5 py-1 ${locale === nextLocale ? "bg-[var(--foreground)] text-[var(--background)]" : "text-[var(--muted-foreground)]"}`}
            aria-pressed={locale === nextLocale}
          >
            {localeLabels[nextLocale]}
          </button>
        ))}
      </div>
      {toastMessage ? (
        <div
          role="status"
          aria-live="polite"
          className="absolute right-0 top-[calc(100%+0.5rem)] z-50 w-72 rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-xs leading-5 text-[var(--foreground)] shadow-panel"
        >
          {toastMessage}
        </div>
      ) : null}
    </div>
  );
}
