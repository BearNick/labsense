"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/labsense/locale-provider";
import { AbnormalMarkersCard } from "@/components/labsense/abnormal-markers-card";
import { AnalysisSummaryCard } from "@/components/labsense/analysis-summary-card";
import { DisclaimerNote } from "@/components/labsense/disclaimer-note";
import { InterpretationCard } from "@/components/labsense/interpretation-card";
import { LifestyleRecommendationsCard } from "@/components/labsense/lifestyle-recommendations-card";
import { PageShell } from "@/components/labsense/page-shell";
import { RecommendationsCard } from "@/components/labsense/recommendations-card";
import { ResultsPaymentCTA } from "@/components/labsense/results-payment-cta";
import { readAnalysisSession, readAnalysisSessionLocale } from "@/lib/analysis-session";
import { buildMarkerRenderingState } from "@/lib/marker-rendering";
import type { Locale } from "@/lib/i18n";
import type { AnalysisSessionData } from "@/lib/types";

export default function ResultsPage() {
  const { locale: currentUiLanguage, messages } = useI18n();
  const [result, setResult] = useState<AnalysisSessionData | null>(null);
  const [reportLanguage, setReportLanguage] = useState<Locale | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setResult(readAnalysisSession());
    setReportLanguage(readAnalysisSessionLocale());
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <PageShell title={messages.results.title} subtitle={messages.results.loadingSubtitle}>
        <article className="text-theme-body rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-6 text-sm leading-6 shadow-panel">
          {messages.results.loadingBody}
        </article>
      </PageShell>
    );
  }

  if (!result) {
    return (
      <PageShell title={messages.results.title} subtitle={messages.results.emptySubtitle}>
        <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-6 shadow-panel">
          <p className="text-theme-body text-sm leading-6">
            {messages.results.emptyBody}
          </p>
          <Link
            href="/upload"
            className="mt-5 inline-flex rounded-full bg-[var(--foreground)] px-5 py-3 text-sm font-medium text-[var(--background)]"
          >
            {messages.results.emptyCta}
          </Link>
        </article>
      </PageShell>
    );
  }

  const effectiveReportLanguage = reportLanguage ?? currentUiLanguage;
  const markerRendering = buildMarkerRenderingState({
    markers: result.markers,
    abnormalMarkers: result.abnormalMarkers
  });

  return (
    <PageShell title={messages.results.title} subtitle={messages.results.subtitle}>
      <AnalysisSummaryCard
        summary={result.summary}
        riskStatus={result.riskStatus}
        reportLanguage={effectiveReportLanguage}
        parseMeta={result.parseMeta}
      />
      <InterpretationCard
        interpretation={{
          ...result.interpretation,
          text: result.interpretation.text
        }}
        riskStatus={result.riskStatus}
        extractionIssue={result.parseMeta.extractionIssue}
        limited={result.parseMeta.decisionKind === "limited"}
      />
      <LifestyleRecommendationsCard text={result.lifestyleRecommendations} />
      <RecommendationsCard
        items={result.recommendations}
        riskStatus={result.riskStatus}
        extractionIssue={result.parseMeta.extractionIssue}
        limited={result.parseMeta.decisionKind === "limited"}
      />
      <AbnormalMarkersCard
        markers={markerRendering.markers}
        allMarkersCount={markerRendering.allMarkersCount}
        extractionIssue={result.parseMeta.extractionIssue}
      />
      <ResultsPaymentCTA />
      <DisclaimerNote />
    </PageShell>
  );
}
