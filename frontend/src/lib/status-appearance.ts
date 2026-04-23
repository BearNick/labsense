import type { Marker, RiskStatus } from "@/lib/types";

export type StatusTone = "normal" | "borderline" | "significant" | "critical";

function inferCritical(label: string, explanation: string): boolean {
  const normalized = `${label} ${explanation}`.toLowerCase();
  return ["critical", "urgent", "urgente", "crit", "сроч", "крит"].some((token) => normalized.includes(token));
}

export function resolveStatusTone(riskStatus?: RiskStatus | null, extractionIssue = false): StatusTone {
  if (extractionIssue) return "borderline";
  if (!riskStatus) return "normal";
  if (riskStatus.color_key === "green") return "normal";
  if (riskStatus.color_key === "yellow") return "borderline";
  return inferCritical(riskStatus.label, riskStatus.explanation) ? "critical" : "significant";
}

export function getStatusAppearance(tone: StatusTone) {
  const map = {
    normal: {
      badge: "border-[color:var(--status-normal-border)] bg-[color:var(--status-normal-soft)] text-[color:var(--status-normal-strong)]",
      hero: "border-[color:var(--status-normal-border)] bg-[linear-gradient(135deg,var(--status-normal-soft),rgba(255,255,255,0.72))]",
      panel: "border-[color:var(--status-normal-border)] bg-[color:var(--status-normal-surface)]",
      accent: "bg-[color:var(--status-normal-strong)]",
      iconWrap: "bg-[color:var(--status-normal-soft)] text-[color:var(--status-normal-strong)]"
    },
    borderline: {
      badge: "border-[color:var(--status-borderline-border)] bg-[color:var(--status-borderline-soft)] text-[color:var(--status-borderline-strong)]",
      hero: "border-[color:var(--status-borderline-border)] bg-[linear-gradient(135deg,var(--status-borderline-soft),rgba(255,255,255,0.72))]",
      panel: "border-[color:var(--status-borderline-border)] bg-[color:var(--status-borderline-surface)]",
      accent: "bg-[color:var(--status-borderline-strong)]",
      iconWrap: "bg-[color:var(--status-borderline-soft)] text-[color:var(--status-borderline-strong)]"
    },
    significant: {
      badge: "border-[color:var(--status-significant-border)] bg-[color:var(--status-significant-soft)] text-[color:var(--status-significant-strong)]",
      hero: "border-[color:var(--status-significant-border)] bg-[linear-gradient(135deg,var(--status-significant-soft),rgba(255,255,255,0.72))]",
      panel: "border-[color:var(--status-significant-border)] bg-[color:var(--status-significant-surface)]",
      accent: "bg-[color:var(--status-significant-strong)]",
      iconWrap: "bg-[color:var(--status-significant-soft)] text-[color:var(--status-significant-strong)]"
    },
    critical: {
      badge: "border-[color:var(--status-critical-border)] bg-[color:var(--status-critical-soft)] text-[color:var(--status-critical-strong)]",
      hero: "border-[color:var(--status-critical-border)] bg-[linear-gradient(135deg,var(--status-critical-soft),rgba(255,255,255,0.7))]",
      panel: "border-[color:var(--status-critical-border)] bg-[color:var(--status-critical-surface)]",
      accent: "bg-[color:var(--status-critical-strong)]",
      iconWrap: "bg-[color:var(--status-critical-soft)] text-[color:var(--status-critical-strong)]"
    }
  } as const;

  return map[tone];
}

export function getMarkerAppearance(status: Marker["status"]) {
  const map = {
    high: {
      badge: "border-[color:var(--marker-high-border)] bg-[color:var(--marker-high-soft)] text-[color:var(--marker-high-strong)]",
      item: "border-[color:var(--marker-high-border)] bg-[linear-gradient(180deg,var(--card),var(--marker-high-surface))]",
      value: "text-[color:var(--marker-high-strong)]"
    },
    low: {
      badge: "border-[color:var(--marker-low-border)] bg-[color:var(--marker-low-soft)] text-[color:var(--marker-low-strong)]",
      item: "border-[color:var(--marker-low-border)] bg-[linear-gradient(180deg,var(--card),var(--marker-low-surface))]",
      value: "text-[color:var(--marker-low-strong)]"
    },
    normal: {
      badge: "border-[color:var(--marker-normal-border)] bg-[color:var(--marker-normal-soft)] text-[color:var(--marker-normal-strong)]",
      item: "border-[color:var(--marker-normal-border)] bg-[linear-gradient(180deg,var(--card),var(--marker-normal-surface))]",
      value: "text-[color:var(--marker-normal-strong)]"
    },
    unknown: {
      badge: "border-[color:var(--marker-neutral-border)] bg-[color:var(--marker-neutral-soft)] text-[color:var(--marker-neutral-strong)]",
      item: "border-[color:var(--marker-neutral-border)] bg-[linear-gradient(180deg,var(--card),var(--marker-neutral-surface))]",
      value: "text-[var(--foreground)]"
    }
  } as const;

  return map[status];
}
