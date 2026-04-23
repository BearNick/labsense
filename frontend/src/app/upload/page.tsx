"use client";

import { useI18n } from "@/components/labsense/locale-provider";
import { DisclaimerNote } from "@/components/labsense/disclaimer-note";
import { UploadCard } from "@/components/labsense/upload-card";
import { PageShell } from "@/components/labsense/page-shell";
import { PaymentSection } from "@/components/labsense/payment-section";
import { getPaymentLinks } from "@/lib/payment-links";

export default function UploadPage() {
  const { messages } = useI18n();
  const links = getPaymentLinks();

  return (
    <PageShell title={messages.uploadPage.title} subtitle={messages.uploadPage.subtitle}>
      <section className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-4">
          <UploadCard />
          <DisclaimerNote compact />
        </div>
        <PaymentSection
          links={links}
          eyebrow={messages.premium.uploadEyebrow}
          title={messages.premium.uploadTitle}
          description={messages.premium.uploadDescription}
          features={messages.premium.uploadFeatures}
          note={messages.premium.telegramNote}
        />
      </section>
    </PageShell>
  );
}
