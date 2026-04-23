import { analysisSessionDataSchema } from "@/lib/labsense-contract";
import { buildMarkers } from "@/lib/analysis-transform";
import { isLocale, type Locale } from "@/lib/i18n";
import type { AnalysisSessionData } from "@/lib/types";

const KEY = "labsense:last-analysis";
const LOCALE_KEY = "labsense:last-analysis-locale";
const ACTIVE_UPLOAD_KEY = "labsense:active-upload";

export function beginAnalysisUpload(uploadId: string) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(ACTIVE_UPLOAD_KEY, uploadId);
  window.sessionStorage.removeItem(KEY);
  window.sessionStorage.removeItem(LOCALE_KEY);
}

export function isActiveAnalysisUpload(uploadId: string): boolean {
  if (typeof window === "undefined") return false;
  return window.sessionStorage.getItem(ACTIVE_UPLOAD_KEY) === uploadId;
}

export function saveAnalysisSession(data: AnalysisSessionData, locale?: Locale) {
  if (typeof window === "undefined") return;
  if (!isActiveAnalysisUpload(data.uploadId)) return;
  window.sessionStorage.setItem(KEY, JSON.stringify(data));
  if (locale) {
    window.sessionStorage.setItem(LOCALE_KEY, locale);
  }
}

export function readAnalysisSession(): AnalysisSessionData | null {
  if (typeof window === "undefined") return null;
  const raw = window.sessionStorage.getItem(KEY);
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw);
    const session = analysisSessionDataSchema.parse(parsed);
    if (!isActiveAnalysisUpload(session.uploadId)) {
      return null;
    }
    if (!Object.keys(session.rawValues).length) {
      return session;
    }

    const markers = session.markers.length ? session.markers : buildMarkers(session.rawValues);
    const abnormalMarkers = session.parseMeta.extractionIssue
      ? []
      : markers.filter((marker) => marker.status === "high" || marker.status === "low");

    if (process.env.NODE_ENV !== "production") {
      console.debug("[analysis-session] raw_values from session", session.rawValues);
      console.debug("[analysis-session] final marker objects", markers);
    }

    return {
      ...session,
      markers,
      abnormalMarkers
    };
  } catch {
    return null;
  }
}

export function clearAnalysisSession() {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(KEY);
  window.sessionStorage.removeItem(LOCALE_KEY);
  window.sessionStorage.removeItem(ACTIVE_UPLOAD_KEY);
}

export function readAnalysisSessionLocale(): Locale | null {
  if (typeof window === "undefined") return null;
  const raw = window.sessionStorage.getItem(LOCALE_KEY);
  return raw && isLocale(raw) ? raw : null;
}
