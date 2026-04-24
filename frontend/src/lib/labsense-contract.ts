import { z } from "zod";

const localizedTextVariantsSchema = z.object({
  en: z.string().optional(),
  ru: z.string().optional(),
  es: z.string().optional()
});

export const markerStatusSchema = z.enum(["normal", "high", "low", "unknown"]);

export const markerSchema = z.object({
  name: z.string(),
  value: z.string(),
  numericValue: z.number().nullable(),
  unit: z.string().nullable(),
  reference: z.string().nullable(),
  status: markerStatusSchema
});

export const parsedLabValueSchema = z.object({
  name: z.string(),
  value: z.number().nullable(),
  unit: z.string().nullable(),
  reference_range: z.string().nullable(),
  status: z.string().default("unknown"),
  category: z.string().default("general")
});

export const analysisSummarySchema = z.object({
  title: z.string(),
  capturedAt: z.string(),
  labSource: z.string(),
  overview: z.string(),
  confidence: z.string()
});

export const recommendationSchema = z.object({
  title: z.string(),
  detail: z.string()
});

export const riskStatusSchema = z.object({
  label: z.string(),
  color_key: z.enum(["green", "yellow", "red"]),
  explanation: z.string(),
  priority_notes: z.array(z.string()).default([])
});

export const paymentLinksSchema = z.object({
  stripe: z.string().url(),
  paypal: z.string().url(),
  telegramStarsPlaceholder: z.string().min(1)
});

export const parseUploadResponseSchema = z.object({
  analysis_id: z.string().optional(),
  values: z.array(parsedLabValueSchema).default([]),
  source: z.string(),
  selected_source: z.string().optional(),
  selection_reason: z.string().optional(),
  initial_source: z.string().optional(),
  final_source: z.string().optional(),
  fallback_used: z.boolean().optional(),
  fallback_reason: z.string().nullable().optional(),
  confidence_score: z.number().int().min(0).max(100).optional(),
  confidence_level: z.enum(["high", "medium", "low"]).optional(),
  confidence_reasons: z.array(z.string()).default([]),
  confidence_explanation: z.string().optional(),
  reference_coverage: z.number().min(0).max(1).optional(),
  unit_coverage: z.number().min(0).max(1).optional(),
  structural_consistency: z.number().min(0).max(1).optional(),
  raw_values: z.record(z.string(), z.number().nullable()),
  extracted_count: z.number().int().nonnegative(),
  warnings: z.array(z.string()).default([])
});

export const parseContextSchema = z.object({
  extracted_count: z.number().int().nonnegative().optional(),
  confidence_score: z.number().int().min(0).max(100).optional(),
  confidence_level: z.enum(["high", "medium", "low"]).optional(),
  confidence_explanation: z.string().optional(),
  reference_coverage: z.number().min(0).max(1).optional(),
  unit_coverage: z.number().min(0).max(1).optional(),
  structural_consistency: z.number().min(0).max(1).optional(),
  fallback_used: z.boolean().optional(),
  warnings: z.array(z.string()).default([]),
  source: z.string().optional()
});

export const interpretLabDataRequestSchema = z.object({
  age: z.number().int().min(1).max(120).nullable(),
  gender: z.string().trim().min(1),
  language: z.enum(["en", "ru", "es"]),
  raw_values: z.record(z.string(), z.number().nullable()),
  parse_context: parseContextSchema.optional()
});

export const interpretLabDataResponseSchema = z.object({
  interpretation: z.string(),
  risk_status: riskStatusSchema.nullish(),
  lifestyle_recommendations: z.string().nullable().optional(),
  meta: z
    .object({
      language: z.string().optional(),
      markers_supplied: z.number().optional(),
      extraction_issue: z.boolean().optional(),
      decision_kind: z.enum(["full", "limited", "extraction_issue"]).optional(),
      status_label: z.string().optional(),
      status_explanation: z.string().optional(),
      summary_overview: z.string().optional(),
      confidence_text: z.string().optional(),
      confidence_score: z.number().int().min(0).max(100).optional(),
      confidence_level: z.enum(["high", "medium", "low"]).optional(),
      confidence_explanation: z.string().optional(),
      recommendation_title: z.string().optional(),
      recommended_action: z.string().optional(),
      hide_marker_counts: z.boolean().optional(),
      hide_priority_notes: z.boolean().optional(),
      gating_reasons: z.array(z.string()).optional()
    })
    .passthrough()
    .default({})
});

export const interpretationStateSchema = z.object({
  status: z.enum(["ready", "unavailable"]),
  text: z.string(),
  error: z.string().nullable(),
  translations: localizedTextVariantsSchema.default({})
});

export const analysisSessionDataSchema = z.object({
  uploadId: z.string().min(1),
  summary: analysisSummarySchema,
  riskStatus: riskStatusSchema.nullish(),
  lifestyleRecommendations: z.string().nullable().default(null),
  lifestyleRecommendationsByLocale: localizedTextVariantsSchema.default({}),
  rawValues: z.record(z.string(), z.number().nullable()).default({}),
  markers: z.array(markerSchema),
  abnormalMarkers: z.array(markerSchema),
  interpretation: interpretationStateSchema,
  recommendations: z.array(recommendationSchema),
  parseMeta: z.object({
    source: z.string(),
    extractedCount: z.number().int().nonnegative(),
    warnings: z.array(z.string()),
    extractionIssue: z.boolean().default(false),
    confidenceScore: z.number().int().min(0).max(100).nullable().default(null),
    confidenceLevel: z.enum(["high", "medium", "low"]).nullable().default(null),
    confidenceExplanation: z.string().nullable().default(null),
    decisionKind: z.enum(["full", "limited", "extraction_issue"]).default("full"),
    statusLabel: z.string().nullable().default(null),
    statusExplanation: z.string().nullable().default(null),
    recommendationTitle: z.string().nullable().default(null),
    hideMarkerCounts: z.boolean().default(false),
    hidePriorityNotes: z.boolean().default(false),
    recommendedAction: z.string().nullable().default(null)
  })
});

export const apiErrorSchema = z.object({
  error: z.string().optional(),
  message: z.string().optional(),
  detail: z
    .union([
      z.string(),
      z.object({
        error: z.string().optional(),
        message: z.string().optional()
      })
    ])
    .optional()
});

export type MarkerContract = z.infer<typeof markerSchema>;
export type AnalysisSessionContract = z.infer<typeof analysisSessionDataSchema>;
export type ParseUploadResponseContract = z.infer<typeof parseUploadResponseSchema>;
export type InterpretLabDataRequestContract = z.infer<typeof interpretLabDataRequestSchema>;
export type InterpretLabDataResponseContract = z.infer<typeof interpretLabDataResponseSchema>;
export type PaymentLinksContract = z.infer<typeof paymentLinksSchema>;
