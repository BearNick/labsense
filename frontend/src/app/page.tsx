"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/labsense/locale-provider";
import { PageShell } from "@/components/labsense/page-shell";
import { AnalysisSummaryCard } from "@/components/labsense/analysis-summary-card";
import { AbnormalMarkersCard } from "@/components/labsense/abnormal-markers-card";
import { RotatingHeroTitle } from "@/components/labsense/rotating-hero-title";
import { readAnalysisSession } from "@/lib/analysis-session";
import { buildSummaryMessaging } from "@/lib/analysis-transform";
import { buildMarkerRenderingState } from "@/lib/marker-rendering";
import type { AnalysisSessionData, AnalysisSummary, Marker } from "@/lib/types";

export default function LandingPage() {
  const { locale, messages } = useI18n();
  const [localResult, setLocalResult] = useState<AnalysisSessionData | null>(null);
  const [summary, setSummary] = useState<AnalysisSummary | null>(null);
  const [markers, setMarkers] = useState<Marker[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const sessionResult = readAnalysisSession();
    setLocalResult(sessionResult);

    if (sessionResult) {
      setSummary({
        ...sessionResult.summary,
        ...buildSummaryMessaging({
          extractedCount: sessionResult.parseMeta.extractedCount,
          warnings: sessionResult.parseMeta.warnings,
          markers: sessionResult.markers,
          riskStatus: sessionResult.riskStatus,
          locale,
          extractionIssue: sessionResult.parseMeta.extractionIssue,
          decisionKind: sessionResult.parseMeta.decisionKind,
          overviewText: sessionResult.summary.overview,
          confidenceText: sessionResult.summary.confidence
        })
      });
      setMarkers(sessionResult.markers);
    } else {
      setSummary(null);
      setMarkers([]);
    }

    setLoading(false);
  }, [locale]);

  const markerRendering = localResult
    ? buildMarkerRenderingState({
        markers: localResult.markers,
        abnormalMarkers: localResult.abnormalMarkers
      })
    : null;

  return (
    <PageShell
      title={
        <RotatingHeroTitle
          leading={messages.landing.heroRotation.leading}
          words={messages.landing.heroRotation.words}
          trailing={messages.landing.heroRotation.trailing}
        />
      }
      subtitle={messages.landing.subhead}
    >
      {loading ? (
        <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-6 text-sm leading-6 text-[var(--muted-foreground)] shadow-panel">
          {messages.landing.loading}
        </article>
      ) : (
        <>
          <section className="grid gap-4 lg:items-stretch lg:grid-cols-[minmax(0,1.08fr)_minmax(340px,0.92fr)]">
            <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-6 shadow-panel md:p-8">
              <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted-foreground)]">{messages.common.appTag}</p>
              <h3 className="mt-4 max-w-2xl text-2xl font-semibold tracking-[-0.03em] text-[var(--foreground)]">
                {messages.landing.title}
              </h3>
              <p className="mt-4 max-w-xl text-sm leading-6 text-[var(--muted-foreground)]">
                {messages.landing.description}
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/upload"
                  className="rounded-full bg-[var(--foreground)] px-5 py-3 text-sm font-medium text-[var(--background)]"
                >
                  {messages.landing.ctaPrimary}
                </Link>
                <Link
                  href="/results"
                  className="rounded-full border border-[var(--border)] px-5 py-3 text-sm font-medium text-[var(--foreground)]"
                >
                  {messages.landing.ctaSecondary}
                </Link>
              </div>
              <div className="mt-8 rounded-[1.5rem] border border-[var(--border)] bg-[var(--background)] p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted-foreground)]">{messages.landing.premiumEyebrow}</p>
                <p className="mt-2 text-sm leading-6 text-[var(--foreground)]">
                  {messages.landing.premiumDescription}
                </p>
              </div>
            </article>
            {localResult && summary ? (
              <div className="min-w-0">
                <AnalysisSummaryCard
                  summary={summary}
                  eyebrow={messages.summaryCard.eyebrow}
                  riskStatus={localResult.riskStatus}
                  parseMeta={localResult.parseMeta}
                />
              </div>
            ) : (
              <article className="flex h-full min-h-[22rem] flex-col justify-between overflow-hidden rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-6 shadow-panel md:p-8">
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
                    {messages.summaryCard.emptyEyebrow}
                  </p>
                  <div className="mt-4 inline-flex rounded-full border border-[var(--border)] bg-[var(--background)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
                    {messages.common.pdf}
                  </div>
                  <h3 className="mt-4 max-w-md text-[1.8rem] font-semibold leading-tight tracking-[-0.04em] text-[var(--foreground)] md:text-[2.05rem]">
                    {messages.summaryCard.emptyTitle}
                  </h3>
                  <p className="mt-4 max-w-xl text-sm leading-6 text-[var(--muted-foreground)]">
                    {messages.summaryCard.emptyBody}
                  </p>
                </div>
                <div className="mt-6 rounded-[1.5rem] border border-[var(--border)] bg-[var(--background)] p-4">
                  <p className="text-sm leading-6 text-[var(--foreground)]">{messages.summaryCard.emptyFootnote}</p>
                </div>
              </article>
            )}
          </section>

          {localResult ? (
            <AbnormalMarkersCard
              markers={markerRendering?.markers ?? []}
              allMarkersCount={markerRendering?.allMarkersCount ?? markers.length}
              extractionIssue={localResult.parseMeta.extractionIssue}
            />
          ) : null}
        </>
      )}
    </PageShell>
  );
}
