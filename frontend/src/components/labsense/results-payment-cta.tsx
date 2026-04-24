"use client";

import { ArrowUpRight, CreditCard, Wallet } from "lucide-react";

import { useI18n } from "@/components/labsense/locale-provider";
import { getPaymentLinks } from "@/lib/payment-links";

function PaymentLink({
  href,
  label,
  icon: Icon,
  accentClassName
}: {
  href: string;
  label: string;
  icon: typeof CreditCard;
  accentClassName: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={`group inline-flex min-h-14 w-full items-center justify-center gap-3 rounded-[1.4rem] px-5 py-4 text-center text-sm font-semibold text-[var(--background)] shadow-[0_16px_36px_rgba(16,24,30,0.18)] transition duration-200 hover:scale-[1.03] hover:brightness-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--foreground)]/20 ${accentClassName}`}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span>{label}</span>
      <ArrowUpRight className="h-4 w-4 shrink-0 opacity-80 transition group-hover:opacity-100" />
    </a>
  );
}

export function ResultsPaymentCTA() {
  const { messages } = useI18n();
  const links = getPaymentLinks();

  return (
    <section className="overflow-hidden rounded-[2rem] border border-[var(--border)] bg-[linear-gradient(180deg,color-mix(in_srgb,var(--card)_90%,white_10%),var(--card))] p-5 shadow-panel md:p-7">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="text-xl font-semibold tracking-[-0.03em] text-[var(--foreground)] md:text-2xl">
          {messages.payments.resultsCtaTitle}
        </h2>
        <p className="mt-3 text-sm leading-6 text-[var(--muted-foreground)]">
          {messages.payments.resultsCtaSubtitle}
        </p>
      </div>
      <div className="mx-auto mt-5 grid max-w-2xl gap-3 sm:grid-cols-2">
        <PaymentLink
          href={links.stripe}
          label={messages.payments.resultsCtaStripe}
          icon={CreditCard}
          accentClassName="bg-[linear-gradient(135deg,#10181e,#22323d)] !text-white dark:bg-gradient-to-r dark:from-slate-700 dark:to-slate-600 dark:shadow-[0_18px_40px_rgba(148,163,184,0.22)]"
        />
        <PaymentLink
          href={links.paypal}
          label={messages.payments.resultsCtaPaypal}
          icon={Wallet}
          accentClassName="bg-[linear-gradient(135deg,#0a4ea3,#009cde)]"
        />
      </div>
    </section>
  );
}
