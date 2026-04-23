import {
  apiErrorSchema,
  interpretLabDataRequestSchema,
  interpretLabDataResponseSchema,
  parseUploadResponseSchema
} from "@/lib/labsense-contract";
import { getMessages, isLocale } from "@/lib/i18n";
import type { InterpretLabDataResponse, ParseUploadResponse } from "@/lib/types";

async function parseJsonSafe(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function toErrorMessage(payload: unknown, fallback: string): string {
  const parsed = apiErrorSchema.safeParse(payload);
  if (!parsed.success) return fallback;

  const { message, detail } = parsed.data;
  if (message) return message;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;

  return fallback;
}

export async function uploadLabPdf(file: File, language: string): Promise<ParseUploadResponse> {
  const locale = isLocale(language) ? language : "en";
  const t = getMessages(locale);
  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", language);

  const response = await fetch("/api/labsense/upload-lab-pdf", {
    method: "POST",
    body: formData
  });

  const payload = await parseJsonSafe(response);
  if (!response.ok) {
    throw new Error(toErrorMessage(payload, t.api.parsePdfFallback));
  }

  return parseUploadResponseSchema.parse(payload);
}

export async function interpretLabData(input: {
  age: number | null;
  gender: string;
  language: string;
  raw_values: Record<string, number | null>;
  parse_context?: {
    extracted_count?: number;
    confidence_score?: number;
    confidence_level?: "high" | "medium" | "low";
    confidence_explanation?: string;
    reference_coverage?: number;
    unit_coverage?: number;
    structural_consistency?: number;
    fallback_used?: boolean;
    warnings?: string[];
    source?: string;
  };
}): Promise<InterpretLabDataResponse> {
  const body = interpretLabDataRequestSchema.parse(input);
  const locale = isLocale(body.language) ? body.language : "en";
  const t = getMessages(locale);

  const response = await fetch("/api/labsense/interpret-lab-data", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body)
  });

  const payload = await parseJsonSafe(response);
  if (!response.ok) {
    throw new Error(toErrorMessage(payload, t.api.interpretFallback));
  }

  return interpretLabDataResponseSchema.parse(payload);
}
