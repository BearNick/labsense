"use client";

import { FileUp, LoaderCircle, ScanSearch } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useI18n } from "@/components/labsense/locale-provider";
import { buildSessionData } from "@/lib/analysis-transform";
import { beginAnalysisUpload, isActiveAnalysisUpload, saveAnalysisSession } from "@/lib/analysis-session";
import type { Locale, Messages } from "@/lib/i18n";
import { interpretLabData, uploadLabPdf } from "@/lib/labsense-api";

const MAX_FILE_BYTES = 10 * 1024 * 1024;

type SubmissionStage = "idle" | "uploading" | "interpreting";

function validateUpload(file: File | null, age: number, errors: Messages["uploadForm"]["errors"]): string | null {
  if (!file) return errors.missingFile;
  if (!file.name.toLowerCase().endsWith(".pdf")) return errors.invalidType;
  if (file.size === 0) return errors.emptyFile;
  if (file.size > MAX_FILE_BYTES) return errors.tooLarge;
  if (!Number.isInteger(age) || age < 1 || age > 120) return errors.invalidAge;
  return null;
}

function createUploadId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export function UploadCard() {
  const router = useRouter();
  const { locale, messages } = useI18n();
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState<Locale>(locale);
  const [gender, setGender] = useState("male");
  const [age, setAge] = useState(35);
  const [stage, setStage] = useState<SubmissionStage>("idle");
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);

  useEffect(() => {
    setLanguage(locale);
  }, [locale]);

  const fileLabel = useMemo(() => {
    if (!file) return messages.uploadForm.chooseFile;
    return file.name;
  }, [file, messages.uploadForm.chooseFile]);

  const loading = stage !== "idle";
  const buttonLabel =
    stage === "uploading"
      ? messages.uploadForm.parsing
      : stage === "interpreting"
        ? messages.uploadForm.interpreting
        : messages.uploadForm.submit;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setWarning(null);

    const validationError = validateUpload(file, age, messages.uploadForm.errors);
    if (validationError) {
      setError(validationError);
      return;
    }

    const uploadId = createUploadId();
    beginAnalysisUpload(uploadId);
    setStage("uploading");

    try {
      const parseResult = await uploadLabPdf(file as File, language);
      if (!isActiveAnalysisUpload(uploadId)) {
        return;
      }
      setWarning(parseResult.warnings[0] ?? null);

      setStage("interpreting");

      try {
        const interpretationResult = await interpretLabData({
          age,
          gender,
          language,
          raw_values: parseResult.raw_values,
          parse_context: {
            extracted_count: parseResult.extracted_count,
            confidence_score: parseResult.confidence_score,
            confidence_level: parseResult.confidence_level,
            confidence_explanation: parseResult.confidence_explanation,
            reference_coverage: parseResult.reference_coverage,
            unit_coverage: parseResult.unit_coverage,
            structural_consistency: parseResult.structural_consistency,
            fallback_used: parseResult.fallback_used,
            warnings: parseResult.warnings,
            source: parseResult.source
          }
        });
        if (!isActiveAnalysisUpload(uploadId)) {
          return;
        }

        saveAnalysisSession(buildSessionData({ uploadId, parseResult, interpretationResult, locale: language }), language);
      } catch (interpretError) {
        if (!isActiveAnalysisUpload(uploadId)) {
          return;
        }
        saveAnalysisSession(
          buildSessionData({
            uploadId,
            parseResult,
            interpretationError:
              interpretError instanceof Error ? interpretError.message : messages.uploadForm.errors.interpretationUnavailable,
            locale: language
          }),
          language
        );
      }

      if (!isActiveAnalysisUpload(uploadId)) {
        return;
      }
      router.push("/results");
    } catch (uploadError) {
      if (!isActiveAnalysisUpload(uploadId)) {
        return;
      }
      setError(uploadError instanceof Error ? uploadError.message : messages.uploadForm.errors.uploadFailed);
    } finally {
      if (isActiveAnalysisUpload(uploadId)) {
        setStage("idle");
      }
    }
  }

  return (
    <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-6 shadow-panel md:p-8">
      <div className="mb-6">
        <div>
          <p className="inline-flex items-center gap-2 rounded-full bg-[var(--secondary)] px-3 py-1 text-xs text-[var(--muted-foreground)]">
            <ScanSearch className="h-3.5 w-3.5" />
            {messages.uploadForm.badge}
          </p>
          <h2 className="mt-4 text-2xl font-semibold tracking-[-0.03em] text-[var(--foreground)] md:text-[2rem]">
            {messages.uploadForm.title}
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted-foreground)]">{messages.uploadForm.description}</p>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <div className="rounded-[1.4rem] bg-[var(--background)] p-4 text-sm leading-6 text-[var(--muted-foreground)]">
            {messages.uploadForm.policy}
          </div>
          <div className="rounded-[1.4rem] bg-[var(--background)] p-4 text-sm leading-6 text-[var(--muted-foreground)]">
            {messages.uploadForm.pdfNotStored}
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="flex cursor-pointer items-center justify-between gap-4 rounded-[1.7rem] border border-dashed border-[var(--border)] bg-[var(--background)] px-5 py-8 text-left transition hover:border-[var(--ring)]">
          <div className="flex items-center gap-4">
            <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--card)] text-[var(--foreground)] shadow-sm">
              <FileUp className="h-5 w-5" />
            </span>
            <span>
              <strong className="block text-sm font-semibold text-[var(--foreground)]">{fileLabel}</strong>
              <span className="text-sm leading-6 text-[var(--muted-foreground)]">
                {messages.common.pdf}
              </span>
              <span className="block text-sm text-[var(--muted-foreground)]">
              {file ? messages.uploadForm.tapToChange : messages.uploadForm.tapToSelect}
              </span>
            </span>
          </div>
          <input
            type="file"
            accept="application/pdf"
            className="hidden"
            disabled={loading}
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>

        <div className="grid gap-3 sm:grid-cols-3">
          <label className="space-y-1">
            <span className="text-xs text-[var(--muted-foreground)]">{messages.uploadForm.language}</span>
            <select
              value={language}
              disabled={loading}
              onChange={(event) => setLanguage(event.target.value as Locale)}
              className="w-full rounded-2xl border border-[var(--border)] bg-[var(--background)] px-3 py-3 text-sm text-[var(--foreground)]"
            >
              <option value="en">English</option>
              <option value="ru">Русский</option>
              <option value="es">Español</option>
            </select>
          </label>

          <label className="space-y-1">
            <span className="text-xs text-[var(--muted-foreground)]">{messages.uploadForm.gender}</span>
            <select
              value={gender}
              disabled={loading}
              onChange={(event) => setGender(event.target.value)}
              className="w-full rounded-2xl border border-[var(--border)] bg-[var(--background)] px-3 py-3 text-sm text-[var(--foreground)]"
            >
              <option value="male">{messages.uploadForm.male}</option>
              <option value="female">{messages.uploadForm.female}</option>
            </select>
          </label>

          <label className="space-y-1">
            <span className="text-xs text-[var(--muted-foreground)]">{messages.uploadForm.age}</span>
            <input
              type="number"
              min={1}
              max={120}
              step={1}
              inputMode="numeric"
              value={age}
              disabled={loading}
              onChange={(event) => setAge(Number.parseInt(event.target.value, 10) || 0)}
              className="w-full rounded-2xl border border-[var(--border)] bg-[var(--background)] px-3 py-3 text-sm text-[var(--foreground)]"
            />
          </label>
        </div>

        {error ? (
          <p className="rounded-2xl border border-[color:var(--danger-strong)]/30 bg-[color:var(--danger-soft)] px-4 py-3 text-sm text-[color:var(--danger-strong)]">
            {error}
          </p>
        ) : null}

        {warning ? (
          <p className="rounded-2xl border border-[color:var(--warning-strong)]/30 bg-[color:var(--warning-soft)] px-4 py-3 text-sm text-[color:var(--warning-strong)]">
            {warning}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={loading}
          className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[var(--foreground)] px-4 py-3.5 text-sm font-medium text-[var(--background)] disabled:opacity-60"
        >
          {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
          {buttonLabel}
        </button>
      </form>
    </article>
  );
}
