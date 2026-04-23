"use client";

import { ArrowUpRight, CreditCard, Sparkles } from "lucide-react";

import { useI18n } from "@/components/labsense/locale-provider";
import type { PaymentLinks } from "@/lib/types";

interface PaymentSectionProps {
  links: PaymentLinks;
  eyebrow?: string;
  title?: string;
  description?: string;
  features?: readonly string[];
  note?: string;
}

function LinkButton({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center justify-center gap-2 rounded-2xl border border-[var(--border)] bg-[var(--background)] px-4 py-3 text-sm font-medium text-[var(--foreground)] transition hover:bg-[var(--secondary)]"
    >
      {label}
      <ArrowUpRight className="h-4 w-4" />
    </a>
  );
}

export function PaymentSection({ links, eyebrow, title, description, features = [], note }: PaymentSectionProps) {
  const { messages } = useI18n();
  const resolvedTitle = title ?? messages.payments.title;
  const resolvedDescription = description ?? messages.payments.description;
  const resolvedNote = note ?? messages.premium.telegramNote ?? messages.payments.telegramStarsPlaceholder ?? links.telegramStarsPlaceholder;

  return (
    <section className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
      {eyebrow ? (
        <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted-foreground)]">{eyebrow}</p>
      ) : null}
      <h3 className="inline-flex items-center gap-2 text-lg font-semibold text-[var(--foreground)]">
        <CreditCard className="h-4 w-4" />
        {resolvedTitle}
      </h3>
      <p className="mt-2 text-sm leading-6 text-[var(--muted-foreground)]">
        {resolvedDescription}
      </p>
      {features.length ? (
        <ul className="mt-4 space-y-2">
          {features.map((feature) => (
            <li key={feature} className="rounded-[1.2rem] bg-[var(--background)] px-4 py-3 text-sm leading-6 text-[var(--foreground)]">
              {feature}
            </li>
          ))}
        </ul>
      ) : null}
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <LinkButton href={links.stripe} label={messages.payments.stripe} />
        <LinkButton href={links.paypal} label={messages.payments.paypal} />
      </div>
      <div className="mt-4 inline-flex items-center gap-2 rounded-full bg-[var(--secondary)] px-3 py-2 text-xs text-[var(--muted-foreground)]">
        <Sparkles className="h-3.5 w-3.5" />
        {resolvedNote}
      </div>
    </section>
  );
}
