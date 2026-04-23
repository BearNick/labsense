import type {
  AnalysisSessionContract,
  InterpretLabDataResponseContract,
  MarkerContract,
  ParseUploadResponseContract,
  PaymentLinksContract,
  riskStatusSchema
} from "@/lib/labsense-contract";
import type { z } from "zod";

export type MarkerStatus = "normal" | "high" | "low" | "unknown";

export type Marker = MarkerContract;

export interface AnalysisSummary {
  title: string;
  capturedAt: string;
  labSource: string;
  overview: string;
  confidence: string;
}

export interface Recommendation {
  title: string;
  detail: string;
}

export type RiskStatus = z.infer<typeof riskStatusSchema>;

export interface PaymentLinks {
  stripe: string;
  paypal: string;
  telegramStarsPlaceholder: string;
}

export interface HistoryItem {
  id: string;
  date: string;
  status: "ready" | "processing";
  highlights: string;
}

export interface AccountProfile {
  fullName: string;
  email: string;
  plan: string;
  locale: "en" | "ru" | "es";
}

export type ParseUploadResponse = ParseUploadResponseContract;

export interface InterpretationState {
  status: "ready" | "unavailable";
  text: string;
  error: string | null;
}

export type InterpretLabDataResponse = InterpretLabDataResponseContract;
export type AnalysisSessionData = AnalysisSessionContract;
export type PaymentLinksConfig = PaymentLinksContract;
