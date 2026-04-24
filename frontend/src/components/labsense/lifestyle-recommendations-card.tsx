"use client";

import { Leaf } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { useI18n } from "@/components/labsense/locale-provider";

interface LifestyleRecommendationsCardProps {
  text?: string | null;
  startDelayMs?: number;
}

const STEP_MS = 18;
const CHUNK_SIZE = 2;

export function LifestyleRecommendationsCard({
  text,
  startDelayMs = 350
}: LifestyleRecommendationsCardProps) {
  const { messages } = useI18n();
  const [visibleCount, setVisibleCount] = useState(0);
  const trimmedText = text?.trim() ?? "";
  const unavailable = !trimmedText;

  useEffect(() => {
    if (unavailable) {
      setVisibleCount(0);
      return;
    }

    setVisibleCount(0);
    let intervalId: number | null = null;
    const startTimer = window.setTimeout(() => {
      intervalId = window.setInterval(() => {
        setVisibleCount((current) => {
          if (current >= trimmedText.length) {
            if (intervalId !== null) {
              window.clearInterval(intervalId);
            }
            return trimmedText.length;
          }
          return Math.min(current + CHUNK_SIZE, trimmedText.length);
        });
      }, STEP_MS);
    }, startDelayMs);

    return () => {
      window.clearTimeout(startTimer);
      if (intervalId !== null) {
        window.clearInterval(intervalId);
      }
    };
  }, [startDelayMs, trimmedText, unavailable]);

  const renderedText = useMemo(() => {
    if (unavailable) {
      return messages.lifestyleCard.unavailable;
    }
    return trimmedText.slice(0, visibleCount);
  }, [messages.lifestyleCard.unavailable, trimmedText, unavailable, visibleCount]);

  const isTyping = !unavailable && visibleCount < trimmedText.length;

  return (
    <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
      <h2 className="inline-flex items-center gap-2 text-lg font-semibold text-[var(--foreground)]">
        <Leaf className="h-4 w-4" />
        {messages.lifestyleCard.title}
      </h2>
      <div className="bg-theme-subtle mt-4 rounded-[1.4rem] p-4 dark:bg-[var(--background)]">
        {!unavailable && visibleCount === 0 ? (
          <p className="text-theme-muted text-sm leading-6">{messages.lifestyleCard.preparing}</p>
        ) : null}
        <p className="text-theme-body whitespace-pre-line text-sm leading-6">
          {renderedText}
          {isTyping ? <span className="ml-0.5 inline-block h-5 w-0.5 animate-pulse bg-[var(--foreground)] align-[-0.2em]" /> : null}
        </p>
      </div>
    </article>
  );
}
