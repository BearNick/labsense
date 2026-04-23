"use client";

import { UserRound } from "lucide-react";

import { useI18n } from "@/components/labsense/locale-provider";
import { PageShell } from "@/components/labsense/page-shell";
import { PaymentSection } from "@/components/labsense/payment-section";
import { getPaymentLinks } from "@/lib/payment-links";

export default function AccountPage() {
  const { messages } = useI18n();
  const links = getPaymentLinks();

  return (
    <PageShell title={messages.account.title} subtitle={messages.account.subtitle}>
      <section className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
        <h2 className="text-lg font-semibold text-[var(--foreground)]">{messages.account.profile}</h2>
        <p className="mt-4 inline-flex items-center gap-2 text-sm leading-6 text-[var(--muted-foreground)]">
          <UserRound className="h-4 w-4" />
          {messages.account.signInPrompt}
        </p>
      </section>

      <PaymentSection
        links={links}
        eyebrow={messages.premium.accountEyebrow}
        title={messages.premium.accountTitle}
        description={messages.premium.accountDescription}
        features={messages.premium.accountFeatures}
        note={messages.premium.telegramNote}
      />
    </PageShell>
  );
}
