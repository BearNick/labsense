import type {
  AnalysisSessionData,
  AnalysisSummary,
  InterpretLabDataResponse,
  Marker,
  ParseUploadResponse,
  Recommendation
} from "@/lib/types";
import { DEFAULT_LOCALE, formatMessage, getMessages, type Locale } from "@/lib/i18n";
import { parseInterpretationSections } from "@/lib/interpretation-sections";
import { addBaseTextVariant, extractLocalizedTextVariants } from "@/lib/results-localization";
import type { RiskStatus } from "@/lib/types";

type Range = {
  min?: number;
  max?: number;
  unit?: string;
  ref?: string;
};

const METRIC_METADATA: Record<string, Range> = {
  "Гемоглобин": { min: 120, max: 170, unit: "g/L", ref: "120 - 170" },
  Hemoglobin: { min: 120, max: 170, unit: "g/L", ref: "120 - 170" },
  "Лейкоциты": { min: 4, max: 10, unit: "x10^9/L", ref: "4.0 - 10.0" },
  "Тромбоциты": { min: 150, max: 400, unit: "x10^9/L", ref: "150 - 400" },
  "Глюкоза": { min: 3.9, max: 5.5, unit: "mmol/L", ref: "3.9 - 5.5" },
  Glucose: { min: 3.9, max: 5.5, unit: "mmol/L", ref: "3.9 - 5.5" },
  "Креатинин": { min: 53, max: 115, unit: "umol/L", ref: "53 - 115" },
  "Холестерин общий": { max: 5.2, unit: "mmol/L", ref: "< 5.2" },
  "ЛПНП": { max: 3, unit: "mmol/L", ref: "< 3.0" },
  LDL: { max: 3, unit: "mmol/L", ref: "< 3.0" },
  "ЛПВП": { min: 1, unit: "mmol/L", ref: ">= 1.0" },
  HDL: { min: 1, unit: "mmol/L", ref: ">= 1.0" },
  "С-реактивный белок": { min: 0, max: 5, unit: "mg/L", ref: "0 - 5" },
  CRP: { min: 0, max: 5, unit: "mg/L", ref: "0 - 5" },
  ALT: { max: 55, unit: "U/L", ref: "< 55" },
  AST: { max: 40, unit: "U/L", ref: "< 40" },
  "Гематокрит": { min: 36, max: 50, unit: "%", ref: "36 - 50" },
  "Эритроциты": { min: 3.8, max: 5.8, unit: "x10^12/L", ref: "3.8 - 5.8" },
  "СОЭ": { max: 20, unit: "mm/h", ref: "< 20" },
  "Витамин D (25-OH)": { min: 30, max: 100, unit: "ng/mL", ref: "30 - 100" }
};

function formatTimestamp(input: Date, locale: Locale): string {
  const intlLocale = locale === "ru" ? "ru-RU" : locale === "es" ? "es-ES" : "en-GB";

  return new Intl.DateTimeFormat(intlLocale, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(input);
}

function formatSummaryDate(input: Date, locale: Locale): string {
  const intlLocale = locale === "ru" ? "ru-RU" : locale === "es" ? "es-ES" : "en-GB";

  return new Intl.DateTimeFormat(intlLocale, {
    year: "numeric",
    month: "short",
    day: "2-digit"
  }).format(input);
}

export function buildSummaryTitle(locale: Locale, referenceDate?: Date | null): string {
  const t = getMessages(locale);

  if (!referenceDate) {
    return t.generated.latestReport;
  }

  return formatMessage(t.generated.reportFromDate, {
    date: formatSummaryDate(referenceDate, locale)
  });
}

function formatNumericValue(value: number): string {
  if (Number.isInteger(value)) return String(value);
  if (Math.abs(value) >= 100) return value.toFixed(1);
  if (Math.abs(value) >= 10) return value.toFixed(2).replace(/\.?0+$/, "");
  return value.toFixed(3).replace(/\.?0+$/, "");
}

function resolveMarkerStatus(value: number, metadata?: Range): Marker["status"] {
  if (!metadata || (metadata.min === undefined && metadata.max === undefined)) return "unknown";
  if (metadata.min !== undefined && value < metadata.min) return "low";
  if (metadata.max !== undefined && value > metadata.max) return "high";
  return "normal";
}

function markerFromPair(name: string, value: number | null): Marker | null {
  if (value === null || Number.isNaN(value)) return null;

  const metadata = METRIC_METADATA[name];
  const unit = metadata?.unit ?? null;
  const reference = metadata?.ref ?? null;

  return {
    name,
    numericValue: value,
    value: unit ? `${formatNumericValue(value)} ${unit}` : formatNumericValue(value),
    unit,
    reference,
    status: resolveMarkerStatus(value, metadata)
  };
}

function markerFromParsedValue(parsedValue: ParseUploadResponse["values"][number]): Marker | null {
  const value = parsedValue.value;
  if (value === null || Number.isNaN(value)) return null;

  const metadata = METRIC_METADATA[parsedValue.name];
  const unit = parsedValue.unit ?? metadata?.unit ?? null;
  const reference = parsedValue.reference_range ?? metadata?.ref ?? null;

  return {
    name: parsedValue.name,
    numericValue: value,
    value: unit ? `${formatNumericValue(value)} ${unit}` : formatNumericValue(value),
    unit,
    reference,
    status: resolveMarkerStatus(value, metadata)
  };
}

function isEmptyRecommendationLine(line: string): boolean {
  const normalized = line.trim().toLowerCase();
  return [
    "none",
    "none.",
    "no specific action needed",
    "no action needed",
    "нет",
    "нет.",
    "никаких специальных действий не требуется",
    "ninguno",
    "ninguno.",
    "no se necesita ninguna acción específica",
    "no hace falta ninguna acción"
  ].includes(normalized);
}

export function buildSummary(
  parseResult: ParseUploadResponse,
  markers: Marker[],
  riskStatus: RiskStatus | null = null,
  locale: Locale = DEFAULT_LOCALE,
  now = new Date()
): AnalysisSummary {
  return {
    title: buildSummaryTitle(locale, now),
    capturedAt: formatTimestamp(now, locale),
    labSource: parseResult.source,
    ...buildSummaryMessaging({
      extractedCount: parseResult.extracted_count,
      warnings: parseResult.warnings,
      markers,
      riskStatus,
      locale
    })
  };
}

type SummarySeverity = "CRITICAL" | "SIGNIFICANT" | "MODERATE" | "MILD" | "NORMAL";

function getValidatedFindingsMeta(meta: Record<string, unknown> | undefined): Record<string, unknown> | null {
  const validatedFindings = meta?.validated_findings;
  return validatedFindings && typeof validatedFindings === "object" ? (validatedFindings as Record<string, unknown>) : null;
}

function getSummarySeverity(
  locale: Locale,
  riskStatus: RiskStatus | null | undefined,
  meta?: Record<string, unknown>
): { label: string; severity: SummarySeverity | null } {
  const t = getMessages(locale);
  const validatedFindings = getValidatedFindingsMeta(meta);
  const rawSeverity = typeof validatedFindings?.severity === "string" ? validatedFindings.severity.toUpperCase() : null;
  const severity = (
    rawSeverity === "CRITICAL" ||
    rawSeverity === "SIGNIFICANT" ||
    rawSeverity === "MODERATE" ||
    rawSeverity === "MILD" ||
    rawSeverity === "NORMAL"
  )
    ? (rawSeverity as SummarySeverity)
    : null;

  if (!severity) {
    return { label: riskStatus?.label ?? t.riskStatus.green.label, severity: null };
  }

  const labelMap: Record<SummarySeverity, string> = {
    CRITICAL: locale === "ru" ? "Критическое отклонение" : locale === "es" ? "Desviación crítica" : "Critical deviation",
    SIGNIFICANT: locale === "ru" ? "Значимое отклонение" : locale === "es" ? "Desviación significativa" : "Significant deviation",
    MODERATE: locale === "ru" ? "Нужно наблюдение" : locale === "es" ? "Necesita observación" : "Needs observation",
    MILD: locale === "ru" ? "Лёгкое отклонение" : locale === "es" ? "Desviación leve" : "Mild deviation",
    NORMAL: locale === "ru" ? "Норма" : locale === "es" ? "Normal" : "Normal"
  };

  return {
    label: labelMap[severity],
    severity
  };
}

function getAbnormalMarkerCount(markers: Marker[], meta?: Record<string, unknown>): number {
  const validatedFindings = getValidatedFindingsMeta(meta);
  const abnormalMarkers = validatedFindings?.abnormal_markers;
  if (Array.isArray(abnormalMarkers)) {
    return abnormalMarkers.length;
  }
  return markers.filter((marker) => marker.status === "high" || marker.status === "low").length;
}

function getSummaryStatusExplanation(locale: Locale, abnormalCount: number, riskStatus?: RiskStatus | null): string {
  if (abnormalCount > 0) {
    return locale === "ru"
      ? "Обнаружены отклонения в показателях"
      : locale === "es"
        ? "Se detectaron desviaciones en los indicadores"
        : "Deviations were detected in the markers";
  }
  return riskStatus?.explanation ?? getMessages(locale).riskStatus.green.explanation;
}

export function buildSummaryMessaging(input: {
  extractedCount: number;
  warnings: string[];
  markers: Marker[];
  riskStatus?: RiskStatus | null;
  locale?: Locale;
  extractionIssue?: boolean;
  decisionKind?: "full" | "limited" | "extraction_issue";
  overviewText?: string | null;
  confidenceText?: string | null;
  abnormalCount?: number;
}): Pick<AnalysisSummary, "overview" | "confidence"> {
  const locale = input.locale ?? DEFAULT_LOCALE;
  const t = getMessages(locale);
  if (input.overviewText || input.confidenceText) {
    return {
      overview: input.overviewText ?? t.generated.markersExtractedOverview.replace("{count}", String(input.extractedCount)),
      confidence: input.confidenceText ?? formatMessage(t.generated.markersCapturedConfidence, { count: input.extractedCount })
    };
  }

  if (input.extractionIssue || input.decisionKind === "extraction_issue") {
    return {
      overview: t.generated.extractionIssueOverview,
      confidence: t.generated.extractionIssueAction
    };
  }

  const abnormalCount =
    typeof input.abnormalCount === "number"
      ? input.abnormalCount
      : input.markers.filter((marker) => marker.status === "high" || marker.status === "low").length;
  const allMarkersInRange = input.markers.length > 0 && input.markers.every((marker) => marker.status === "normal");
  const overallIsNormal = input.riskStatus?.color_key === "green";
  const warningsSuffix = input.warnings.length ? ` ${input.warnings[0]}` : "";

  const confidence =
    allMarkersInRange && overallIsNormal
      ? formatMessage(t.generated.markersCapturedConfidence, { count: input.extractedCount })
      : abnormalCount
        ? formatMessage(
            abnormalCount === 1 ? t.generated.markersNeedReviewConfidence : t.generated.markersNeedReviewConfidencePlural,
            { count: abnormalCount }
          )
        : formatMessage(t.generated.markersCapturedConfidence, { count: input.extractedCount });

  return {
    overview: `${formatMessage(t.generated.markersExtractedOverview, { count: input.extractedCount })}${warningsSuffix}`,
    confidence
  };
}

export function buildMarkers(
  rawValues: Record<string, number | null>,
  parsedValues: ParseUploadResponse["values"] = []
): Marker[] {
  const sourceMarkers = parsedValues.length
    ? parsedValues.map((parsedValue) => markerFromParsedValue(parsedValue))
    : Object.entries(rawValues).map(([name, value]) => markerFromPair(name, value));

  return sourceMarkers
    .filter((item): item is Marker => item !== null)
    .sort((left, right) => {
      const leftPriority = left.status === "high" || left.status === "low" ? 0 : left.status === "unknown" ? 2 : 1;
      const rightPriority = right.status === "high" || right.status === "low" ? 0 : right.status === "unknown" ? 2 : 1;
      if (leftPriority !== rightPriority) return leftPriority - rightPriority;
      return left.name.localeCompare(right.name);
    });
}

export function buildRecommendations(
  interpretation: string,
  locale: Locale = DEFAULT_LOCALE,
  fallbackError?: string | null,
  extractionIssue = false,
  recommendationTitle?: string | null,
  recommendedAction?: string | null
): Recommendation[] {
  const t = getMessages(locale);
  if (recommendationTitle && recommendedAction) {
    return [
      {
        title: recommendationTitle,
        detail: recommendedAction
      }
    ];
  }

  if (extractionIssue) {
    return [
      {
        title: t.generated.extractionIssueTitle,
        detail: t.generated.extractionIssueAction
      }
    ];
  }

  const sections = parseInterpretationSections(interpretation);
  const nextSteps = sections.find((section) => section.key === "nextSteps")?.lines ?? [];
  const optionalImprovements = sections.find((section) => section.key === "optionalImprovements")?.lines ?? [];
  const actionLines = (nextSteps.length ? nextSteps : optionalImprovements).filter((line) => !isEmptyRecommendationLine(line));

  if (!actionLines.length) {
    if (interpretation.trim()) {
      return [];
    }

    return [
      {
        title: t.generated.clinicalFollowUp,
        detail: fallbackError ?? t.generated.physicianReview
      }
    ];
  }

  return actionLines.slice(0, 4).map((line, index) => ({
    title: formatMessage(t.generated.recommendation, { index: index + 1 }),
    detail: line
  }));
}

export function buildSessionData(input: {
  uploadId: string;
  parseResult: ParseUploadResponse;
  interpretationResult?: InterpretLabDataResponse;
  interpretationError?: string | null;
  locale?: Locale;
}): AnalysisSessionData {
  const locale = input.locale ?? DEFAULT_LOCALE;
  const decisionMeta = input.interpretationResult?.meta;
  const decisionKind = decisionMeta?.decision_kind ?? "full";
  const extractionIssue = decisionMeta?.extraction_issue === true || decisionKind === "extraction_issue";
  const markers = buildMarkers(input.parseResult.raw_values, input.parseResult.values);
  const hidePriorityNotes = decisionMeta?.hide_priority_notes === true;
  const abnormal = extractionIssue ? [] : markers.filter((marker) => marker.status === "high" || marker.status === "low");
  const interpretationText = input.interpretationResult?.interpretation?.trim() ?? "";
  const responseMeta = (input.interpretationResult?.meta ?? {}) as Record<string, unknown>;
  const statusLabel = decisionMeta?.status_label || null;
  const statusExplanation = decisionMeta?.status_explanation || null;
  const confidenceText = decisionMeta?.confidence_text || null;
  const summaryOverview = decisionMeta?.summary_overview || null;
  const recommendedAction = decisionMeta?.recommended_action || null;
  const recommendationTitle = decisionMeta?.recommendation_title || null;
  const confidenceScore = decisionMeta?.confidence_score ?? input.parseResult.confidence_score ?? null;
  const confidenceLevel = decisionMeta?.confidence_level ?? input.parseResult.confidence_level ?? null;
  const confidenceExplanation = decisionMeta?.confidence_explanation ?? input.parseResult.confidence_explanation ?? null;
  const riskStatus = decisionKind !== "extraction_issue" ? (input.interpretationResult?.risk_status ?? null) : null;
  const abnormalCount = extractionIssue ? 0 : getAbnormalMarkerCount(markers, responseMeta);
  const summarySeverity = getSummarySeverity(locale, riskStatus, responseMeta);
  const responseLanguage = typeof decisionMeta?.language === "string" ? decisionMeta.language : input.locale ?? null;
  const interpretationTranslations = addBaseTextVariant(
    extractLocalizedTextVariants(decisionMeta, "interpretation"),
    responseLanguage,
    interpretationText
  );
  const lifestyleRecommendations = input.interpretationResult?.lifestyle_recommendations ?? null;
  const lifestyleRecommendationTranslations = addBaseTextVariant(
    extractLocalizedTextVariants(decisionMeta, "lifestyleRecommendations"),
    responseLanguage,
    lifestyleRecommendations
  );

  if (process.env.NODE_ENV !== "production") {
    console.debug("[analysis-transform] raw_values from API", input.parseResult.raw_values);
    console.debug("[analysis-transform] transformed markers", markers);
  }

  return {
    uploadId: input.uploadId,
    summary: {
      ...buildSummary(input.parseResult, markers, riskStatus, locale),
      ...buildSummaryMessaging({
        extractedCount: input.parseResult.extracted_count,
        warnings: input.parseResult.warnings,
        markers,
        riskStatus,
        locale,
        extractionIssue,
        decisionKind,
        overviewText: summaryOverview,
        confidenceText,
        abnormalCount
      })
    },
    riskStatus,
    lifestyleRecommendations,
    lifestyleRecommendationsByLocale: lifestyleRecommendationTranslations,
    rawValues: input.parseResult.raw_values,
    markers,
    abnormalMarkers: abnormal,
    interpretation: {
      status: interpretationText ? "ready" : "unavailable",
      text: interpretationText,
      error: interpretationText ? null : input.interpretationError ?? getMessages(locale).interpretationCard.unavailable,
      translations: interpretationTranslations
    },
    recommendations: buildRecommendations(
      interpretationText,
      locale,
      input.interpretationError ?? null,
      extractionIssue,
      recommendationTitle,
      recommendedAction
    ),
      parseMeta: {
        source: input.parseResult.source,
        extractedCount: input.parseResult.extracted_count,
        warnings: input.parseResult.warnings,
        extractionIssue,
        confidenceScore,
        confidenceLevel,
        confidenceExplanation,
        decisionKind,
        statusLabel: statusLabel || (!extractionIssue ? summarySeverity.label : null),
        statusExplanation:
          statusExplanation || (!extractionIssue ? getSummaryStatusExplanation(locale, abnormalCount, riskStatus) : null),
        recommendationTitle,
        hideMarkerCounts: decisionMeta?.hide_marker_counts === true,
        hidePriorityNotes,
        recommendedAction
      }
  };
}
