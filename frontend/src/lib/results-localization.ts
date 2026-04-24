import { isLocale, type Locale } from "@/lib/i18n";

type LocalizedTextVariants = Partial<Record<Locale, string>>;

function normalizeLocalizedTextVariants(value: unknown): LocalizedTextVariants {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return {};
  }

  const variants: LocalizedTextVariants = {};
  for (const [key, entryValue] of Object.entries(value)) {
    if (!isLocale(key) || typeof entryValue !== "string") continue;
    const trimmed = entryValue.trim();
    if (trimmed) {
      variants[key] = trimmed;
    }
  }

  return variants;
}

function readNestedValue(source: Record<string, unknown>, path: string[]): unknown {
  let current: unknown = source;
  for (const segment of path) {
    if (!current || typeof current !== "object" || Array.isArray(current)) {
      return null;
    }
    current = (current as Record<string, unknown>)[segment];
  }
  return current;
}

export function extractLocalizedTextVariants(meta: unknown, kind: "interpretation" | "lifestyleRecommendations"): LocalizedTextVariants {
  if (!meta || typeof meta !== "object" || Array.isArray(meta)) {
    return {};
  }

  const source = meta as Record<string, unknown>;
  const candidates =
    kind === "interpretation"
      ? [
          source.interpretation_by_locale,
          source.interpretations_by_locale,
          source.localized_interpretation,
          source.localized_interpretations,
          source.interpretation_translations,
          readNestedValue(source, ["translations", "interpretation"]),
          readNestedValue(source, ["localized", "interpretation"])
        ]
      : [
          source.lifestyle_recommendations_by_locale,
          source.localized_lifestyle_recommendations,
          source.lifestyle_recommendations_translations,
          readNestedValue(source, ["translations", "lifestyle_recommendations"]),
          readNestedValue(source, ["localized", "lifestyle_recommendations"])
        ];

  for (const candidate of candidates) {
    const variants = normalizeLocalizedTextVariants(candidate);
    if (Object.keys(variants).length) {
      return variants;
    }
  }

  return {};
}

export function addBaseTextVariant(
  variants: LocalizedTextVariants,
  locale: string | null | undefined,
  text: string | null | undefined
): LocalizedTextVariants {
  if (!text?.trim() || !locale || !isLocale(locale)) {
    return variants;
  }

  return {
    ...variants,
    [locale]: text.trim()
  };
}

export function resolveLocalizedText(
  baseText: string | null | undefined,
  variants: LocalizedTextVariants | null | undefined,
  locale: Locale
): string {
  const localizedText = variants?.[locale]?.trim();
  if (localizedText) {
    return localizedText;
  }

  return baseText?.trim() ?? "";
}
