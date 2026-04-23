"use client";

import { AlertTriangle, CheckCircle2, TrendingDown, TrendingUp } from "lucide-react";

import { useI18n } from "@/components/labsense/locale-provider";
import { formatMessage } from "@/lib/i18n";
import { getMarkerAppearance } from "@/lib/status-appearance";
import type { Marker } from "@/lib/types";

interface AbnormalMarkersCardProps {
  markers: Marker[];
  allMarkersCount: number;
  extractionIssue?: boolean;
}

export function AbnormalMarkersCard({ markers, allMarkersCount, extractionIssue = false }: AbnormalMarkersCardProps) {
  const { messages } = useI18n();

  if (extractionIssue) {
    return (
      <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
        <h3 className="text-lg font-semibold text-[var(--foreground)]">{messages.markersCard.title}</h3>
        <p className="mt-4 rounded-[1.4rem] bg-[var(--background)] p-4 text-sm leading-6 text-[var(--muted-foreground)]">
          {messages.generated.extractionIssueMarkersHidden}
        </p>
      </article>
    );
  }

  if (!markers.length) {
    return (
      <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
        <h3 className="text-lg font-semibold text-[var(--foreground)]">{messages.markersCard.title}</h3>
        <p className="mt-4 rounded-[1.4rem] bg-[var(--background)] p-4 text-sm leading-6 text-[var(--muted-foreground)]">{messages.markersCard.empty}</p>
      </article>
    );
  }

  return (
    <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
      <h3 className="text-lg font-semibold text-[var(--foreground)]">{messages.markersCard.title}</h3>
      <p className="mt-1 text-sm leading-6 text-[var(--muted-foreground)]">
        {formatMessage(messages.markersCard.showing, { visible: markers.length, total: allMarkersCount })}
      </p>
      <ul className="mt-5 grid grid-cols-1 gap-3 lg:grid-cols-2">
        {markers.map((marker) => {
          const appearance = getMarkerAppearance(marker.status);

          return (
            <li key={marker.name} className={`rounded-[1.4rem] border p-4 ${appearance.item}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[var(--foreground)]">{marker.name}</p>
                  <p className={`mt-1 text-sm font-medium ${appearance.value}`}>{marker.value}</p>
                  <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                    {marker.reference ? `${messages.common.reference} ${marker.reference}` : messages.markersCard.referenceUnavailable}
                  </p>
                </div>
                <span className={`inline-flex shrink-0 items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium ${appearance.badge}`}>
                  {marker.status === "high" ? <TrendingUp className="h-3.5 w-3.5" /> : null}
                  {marker.status === "low" ? <TrendingDown className="h-3.5 w-3.5" /> : null}
                  {marker.status === "unknown" ? <AlertTriangle className="h-3.5 w-3.5" /> : null}
                  {marker.status === "normal" ? <CheckCircle2 className="h-3.5 w-3.5" /> : null}
                  {marker.status === "high" ? messages.markersCard.statusHigh : null}
                  {marker.status === "low" ? messages.markersCard.statusLow : null}
                  {marker.status === "unknown" ? messages.markersCard.statusUnknown : null}
                  {marker.status === "normal" ? messages.markersCard.statusNormal : null}
                </span>
              </div>
            </li>
          );
        })}
      </ul>
      {markers.some((marker) => marker.status === "unknown") ? (
        <p className="mt-4 inline-flex items-center gap-2 rounded-full border border-[color:var(--marker-neutral-border)] bg-[color:var(--marker-neutral-soft)] px-3 py-1 text-xs text-[color:var(--marker-neutral-strong)]">
          <AlertTriangle className="h-3.5 w-3.5" />
          {messages.markersCard.unknownHint}
        </p>
      ) : null}
    </article>
  );
}
