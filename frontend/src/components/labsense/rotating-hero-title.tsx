"use client";

import { useEffect, useMemo, useState } from "react";

type RotatingHeroTitleProps = {
  leading: string;
  words: readonly string[];
  trailing: string;
};

const ROTATION_INTERVAL_MS = 2600;

export function RotatingHeroTitle({ leading, words, trailing }: RotatingHeroTitleProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  const reservedWord = useMemo(
    () => words.reduce((widest, candidate) => (candidate.length > widest.length ? candidate : widest), words[0] ?? ""),
    [words]
  );

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const syncMotionPreference = () => setPrefersReducedMotion(mediaQuery.matches);

    syncMotionPreference();
    mediaQuery.addEventListener("change", syncMotionPreference);

    return () => {
      mediaQuery.removeEventListener("change", syncMotionPreference);
    };
  }, []);

  useEffect(() => {
    if (prefersReducedMotion || words.length <= 1) {
      setActiveIndex(0);
      return;
    }

    const intervalId = window.setInterval(() => {
      setActiveIndex((currentIndex) => (currentIndex + 1) % words.length);
    }, ROTATION_INTERVAL_MS);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [prefersReducedMotion, words]);

  const activeWord = words[activeIndex] ?? "";

  return (
    <>
      <span>{leading}</span>
      <span className="relative inline-block align-baseline whitespace-nowrap">
        <span className="invisible">{reservedWord}</span>
        <span
          key={activeWord}
          aria-hidden="true"
          className="hero-word-fade absolute inset-0 text-[var(--foreground)] motion-reduce:animate-none"
        >
          {activeWord}
        </span>
        <span className="sr-only">{activeWord}</span>
      </span>
      <span>{trailing}</span>
    </>
  );
}
