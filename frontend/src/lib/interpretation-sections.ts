export type InterpretationSectionKey =
  | "overallStatus"
  | "keyObservations"
  | "importance"
  | "whatThisMeans"
  | "optionalImprovements"
  | "nextSteps"
  | "finalConclusion";

export interface ParsedInterpretationSection {
  key: InterpretationSectionKey | null;
  lines: string[];
}

const SECTION_ALIASES: Record<InterpretationSectionKey, string[]> = {
  overallStatus: ["Overall status", "Общий статус", "Estado general"],
  keyObservations: ["Key observations", "Ключевые наблюдения", "Observaciones clave"],
  importance: ["Importance", "Значение", "Importancia"],
  whatThisMeans: ["What this means", "Что это значит", "Qué significa"],
  optionalImprovements: ["Optional improvements", "Что можно улучшить", "Mejoras opcionales"],
  nextSteps: ["Next steps", "Следующие шаги", "Siguientes pasos"],
  finalConclusion: ["Final conclusion", "Итог", "Conclusión final"]
};

const ALIAS_TO_KEY = new Map<string, InterpretationSectionKey>(
  Object.entries(SECTION_ALIASES).flatMap(([key, aliases]) =>
    aliases.map((alias) => [normalizeHeading(alias), key as InterpretationSectionKey])
  )
);

function normalizeHeading(value: string): string {
  return value.trim().replace(/:+$/, "").toLowerCase();
}

function cleanSectionLine(line: string): string {
  return line.replace(/^[-*\d.)\s]+/, "").trim();
}

export function getInterpretationSectionKey(line: string): InterpretationSectionKey | null {
  return ALIAS_TO_KEY.get(normalizeHeading(line)) ?? null;
}

export function parseInterpretationSections(text: string): ParsedInterpretationSection[] {
  const sections: ParsedInterpretationSection[] = [];
  let current: ParsedInterpretationSection | null = null;

  for (const rawLine of text.split(/\n+/)) {
    const line = rawLine.trim();
    if (!line) continue;

    const key = getInterpretationSectionKey(line);
    if (key) {
      if (current) sections.push(current);
      current = { key, lines: [] };
      continue;
    }

    if (!current) {
      current = { key: null, lines: [] };
    }

    const cleaned = cleanSectionLine(line);
    if (cleaned) {
      current.lines.push(cleaned);
    }
  }

  if (current) sections.push(current);
  return sections.filter((section) => section.lines.length || section.key !== null);
}
