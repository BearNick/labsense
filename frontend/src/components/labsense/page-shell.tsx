import type { ReactNode } from "react";

interface PageShellProps {
  title: ReactNode;
  subtitle?: string;
  children: ReactNode;
}

export function PageShell({ title, subtitle, children }: PageShellProps) {
  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-28 pt-6 md:px-8 md:pb-14 md:pt-8">
      <header className="mb-6 rounded-[2rem] border border-[var(--border)] bg-[var(--card)] px-5 py-6 shadow-panel md:mb-8 md:px-8 md:py-8">
        <h1 className="text-[2rem] font-semibold tracking-[-0.04em] text-[var(--foreground)] md:text-[2.6rem]">
          {title}
        </h1>
        {subtitle ? (
          <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)] md:text-base">
            {subtitle}
          </p>
        ) : null}
      </header>
      <section className="space-y-4 md:space-y-6">{children}</section>
    </main>
  );
}
