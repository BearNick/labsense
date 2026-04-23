import type {
  AccountProfile,
  AnalysisSummary,
  HistoryItem,
  Marker,
  PaymentLinks,
  Recommendation
} from "@/lib/types";
import type { Locale } from "@/lib/i18n";
import { buildSummaryTitle } from "@/lib/analysis-transform";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function getMockSummary(locale: Locale = "en"): Promise<AnalysisSummary> {
  await wait(120);
  const capturedAt = "2026-04-22 09:10";
  const referenceDate = new Date("2026-04-22T09:10:00Z");
  const byLocale: Record<Locale, AnalysisSummary> = {
    en: {
      title: buildSummaryTitle("en", referenceDate),
      capturedAt,
      labSource: "City Clinical Lab",
      overview: "Mild inflammatory and lipid deviations, with no obvious acute-risk pattern.",
      confidence: "92% extraction confidence"
    },
    ru: {
      title: buildSummaryTitle("ru", referenceDate),
      capturedAt,
      labSource: "Городская клиническая лаборатория",
      overview: "Небольшие воспалительные и липидные отклонения без явных признаков острого риска.",
      confidence: "Точность извлечения 92%"
    },
    es: {
      title: buildSummaryTitle("es", referenceDate),
      capturedAt,
      labSource: "Laboratorio clínico central",
      overview: "Desviaciones leves en inflamación y perfil lipídico, sin señales evidentes de riesgo agudo.",
      confidence: "92% de precisión en la extracción"
    }
  };

  return byLocale[locale];
}

export async function getMockMarkers(locale: Locale = "en"): Promise<Marker[]> {
  await wait(140);
  const vitaminDName =
    locale === "ru" ? "Витамин D" : locale === "es" ? "Vitamina D" : "Vitamin D";

  return [
    { name: "CRP", value: "8.4 mg/L", numericValue: 8.4, unit: "mg/L", reference: "0.0 - 5.0", status: "high" },
    { name: "LDL", value: "3.9 mmol/L", numericValue: 3.9, unit: "mmol/L", reference: "< 3.0", status: "high" },
    { name: vitaminDName, value: "21 ng/mL", numericValue: 21, unit: "ng/mL", reference: "30 - 100", status: "low" },
    {
      name: locale === "ru" ? "Гемоглобин" : locale === "es" ? "Hemoglobina" : "Hemoglobin",
      value: "141 g/L",
      numericValue: 141,
      unit: "g/L",
      reference: "130 - 170",
      status: "normal"
    }
  ];
}

export async function getMockRecommendations(locale: Locale = "en"): Promise<Recommendation[]> {
  await wait(80);
  const byLocale: Record<Locale, Recommendation[]> = {
    en: [
      {
        title: "Lipid follow-up",
        detail: "Reduce saturated fat intake and repeat the lipid profile in 8 to 10 weeks."
      },
      {
        title: "Inflammation review",
        detail: "Repeat CRP with a CBC and ferritin to confirm whether the elevation persists."
      },
      {
        title: "Vitamin D support",
        detail: "Discuss a maintenance plan with your physician and monitor the level monthly."
      }
    ],
    ru: [
      {
        title: "Контроль липидов",
        detail: "Снизьте долю насыщенных жиров и повторите липидный профиль через 8-10 недель."
      },
      {
        title: "Контроль воспаления",
        detail: "Повторите CRP вместе с общим анализом крови и ферритином, чтобы понять, сохраняется ли повышение."
      },
      {
        title: "Поддержка витамина D",
        detail: "Обсудите с врачом поддерживающую схему и проверьте показатель повторно через месяц."
      }
    ],
    es: [
      {
        title: "Seguimiento lipídico",
        detail: "Reduce las grasas saturadas y repite el perfil lipídico en 8 a 10 semanas."
      },
      {
        title: "Control de inflamación",
        detail: "Repite la CRP con hemograma y ferritina para confirmar si la elevación persiste."
      },
      {
        title: "Apoyo con vitamina D",
        detail: "Consulta con tu médico una pauta de mantenimiento y vuelve a revisar el valor en un mes."
      }
    ]
  };

  return byLocale[locale];
}

export async function getMockPaymentLinks(): Promise<PaymentLinks> {
  await wait(60);
  return {
    stripe: "https://buy.stripe.com/cNibJ2feR8nx0lodvE2go0b",
    paypal: "https://paypal.me/etherealrest",
    telegramStarsPlaceholder: "Telegram Stars integration is coming soon"
  };
}

export async function getMockHistory(locale: Locale = "en"): Promise<HistoryItem[]> {
  await wait(90);
  const byLocale: Record<Locale, HistoryItem[]> = {
    en: [
      { id: "AN-8420", date: "2026-04-22", status: "ready", highlights: "CRP elevated, LDL elevated" },
      { id: "AN-8391", date: "2026-04-04", status: "ready", highlights: "Vitamin D below range" },
      { id: "AN-8357", date: "2026-03-16", status: "processing", highlights: "Interpretation in progress" }
    ],
    ru: [
      { id: "AN-8420", date: "2026-04-22", status: "ready", highlights: "CRP повышен, LDL повышен" },
      { id: "AN-8391", date: "2026-04-04", status: "ready", highlights: "Витамин D ниже нормы" },
      { id: "AN-8357", date: "2026-03-16", status: "processing", highlights: "Интерпретация готовится" }
    ],
    es: [
      { id: "AN-8420", date: "2026-04-22", status: "ready", highlights: "CRP elevada, LDL elevado" },
      { id: "AN-8391", date: "2026-04-04", status: "ready", highlights: "Vitamina D por debajo del rango" },
      { id: "AN-8357", date: "2026-03-16", status: "processing", highlights: "Interpretación en curso" }
    ]
  };

  return byLocale[locale];
}

export async function getMockAccount(locale: Locale = "en"): Promise<AccountProfile> {
  await wait(70);
  const plans: Record<Locale, string> = {
    en: "Labsense Supporter",
    ru: "Поддержка Labsense",
    es: "Apoyo a Labsense"
  };

  return {
    fullName: "Alex Morgan",
    email: "alex@labsense.app",
    plan: plans[locale],
    locale
  };
}
