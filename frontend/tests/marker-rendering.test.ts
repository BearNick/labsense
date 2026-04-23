import assert from "node:assert/strict";

import { buildSessionData } from "../src/lib/analysis-transform";
import { buildMarkerRenderingState } from "../src/lib/marker-rendering";
import type { Marker, ParseUploadResponse } from "../src/lib/types";

function marker(name: string, value: string, status: Marker["status"]): Marker {
  return {
    name,
    value,
    numericValue: null,
    unit: null,
    reference: null,
    status
  };
}

function test(name: string, fn: () => void) {
  try {
    fn();
    console.log(`ok - ${name}`);
  } catch (error) {
    console.error(`not ok - ${name}`);
    throw error;
  }
}

test("western chemistry markers remain renderable when no abnormal markers are present", () => {
  const chemistryMarkers = [
    marker("Sodium", "140 mmol/L", "normal"),
    marker("Potassium", "4.2 mmol/L", "normal"),
    marker("Chloride", "103 mmol/L", "normal"),
    marker("Urea", "5.1 mmol/L", "normal"),
    marker("Creatinine", "89 umol/L", "normal"),
    marker("eGFR", "96 mL/min/1.73m2", "unknown"),
    marker("Glucose", "5.1 mmol/L", "normal"),
    marker("AST", "20 U/L", "normal"),
    marker("ALT", "18 U/L", "normal"),
    marker("HbA1c", "33 mmol/mol", "unknown"),
    marker("Urine Albumin", "3 mg/L", "unknown"),
    marker("Urine Creatinine", "5.6 mmol/L", "unknown"),
    marker("ACR", "<0.1 mg Alb/mmol", "unknown")
  ];

  const rendering = buildMarkerRenderingState({
    markers: chemistryMarkers,
    abnormalMarkers: []
  });

  assert.equal(rendering.markers.length, chemistryMarkers.length);
  assert.equal(rendering.allMarkersCount, chemistryMarkers.length);
  assert.deepEqual(
    rendering.markers.map((item) => item.name),
    chemistryMarkers.map((item) => item.name)
  );
});

test("western CBC markers remain renderable in existing sorted order", () => {
  const cbcMarkers = [
    marker("WBC", "11.2 K/uL", "high"),
    marker("Neutrophils", "8.1 K/uL", "high"),
    marker("HGB", "14.1 g/dL", "normal"),
    marker("HCT", "42 %", "normal"),
    marker("RBC", "5.0 M/uL", "normal"),
    marker("PLT", "240 K/uL", "normal")
  ];

  const rendering = buildMarkerRenderingState({
    markers: cbcMarkers,
    abnormalMarkers: cbcMarkers.filter((item) => item.status === "high" || item.status === "low")
  });

  assert.equal(rendering.markers.length, cbcMarkers.length);
  assert.equal(rendering.allMarkersCount, cbcMarkers.length);
  assert.deepEqual(
    rendering.markers.map((item) => item.name),
    cbcMarkers.map((item) => item.name)
  );
});

test("existing Russian markers remain renderable", () => {
  const russianMarkers = [
    marker("Гемоглобин", "148 g/L", "normal"),
    marker("Лейкоциты", "6.4 x10^9/L", "normal"),
    marker("Тромбоциты", "250 x10^9/L", "normal")
  ];

  const rendering = buildMarkerRenderingState({
    markers: russianMarkers,
    abnormalMarkers: []
  });

  assert.equal(rendering.markers.length, russianMarkers.length);
  assert.equal(rendering.allMarkersCount, russianMarkers.length);
});

test("rendering never falls back to an empty markers state when extracted markers exist", () => {
  const rendering = buildMarkerRenderingState({
    markers: [marker("Glucose", "5.2 mmol/L", "normal")],
    abnormalMarkers: []
  });

  assert.equal(rendering.markers.length, 1);
  assert.equal(rendering.markers[0]?.name, "Glucose");
});

test("final marker-card input preserves extracted western inline references from upload payload", () => {
  const parseResult: ParseUploadResponse = {
    analysis_id: "upload-1",
    source: "pdfplumber",
    selected_source: "text",
    selection_reason: "legacy_text_baseline",
    initial_source: "text",
    final_source: "text",
    fallback_used: false,
    fallback_reason: null,
    confidence_score: 100,
    confidence_level: "high",
    confidence_reasons: ["legacy_text_baseline"],
    confidence_explanation: "Legacy baseline text extraction path is active.",
    reference_coverage: 0,
    unit_coverage: 0,
    structural_consistency: 1,
    extracted_count: 12,
    warnings: [],
    raw_values: {
      Sodium: 141,
      Potassium: 4.1,
      Chloride: 99,
      Urea: 7.1,
      Creatinine: 88,
      "Uric Acid": 0.21,
      AST: 33,
      ALT: 25,
      Glucose: 5.6,
      "Urine Albumin": 1.5,
      "Urine Creatinine": 16.8,
      ACR: 0.1
    },
    values: [
      { name: "Sodium", value: 141, unit: "mmol/L", reference_range: "135-145", status: "unknown", category: "general" },
      { name: "Potassium", value: 4.1, unit: "mmol/L", reference_range: "3.5-5.1", status: "unknown", category: "general" },
      { name: "Chloride", value: 99, unit: "mmol/L", reference_range: "95-110", status: "unknown", category: "general" },
      { name: "Urea", value: 7.1, unit: "mmol/L", reference_range: "3.0-10.0", status: "unknown", category: "general" },
      { name: "Creatinine", value: 88, unit: "umol/L", reference_range: "44-110", status: "unknown", category: "general" },
      { name: "Uric Acid", value: 0.21, unit: "mmol/L", reference_range: "0.15-0.45", status: "unknown", category: "general" },
      { name: "AST", value: 33, unit: "U/L", reference_range: "< 41", status: "unknown", category: "general" },
      { name: "ALT", value: 25, unit: "U/L", reference_range: "< 51", status: "unknown", category: "general" },
      { name: "Glucose", value: 5.6, unit: "mmol/L", reference_range: "3.9 - 6.0", status: "unknown", category: "general" },
      { name: "Urine Albumin", value: 1.5, unit: "mg/L", reference_range: "< 20.1", status: "unknown", category: "general" },
      { name: "Urine Creatinine", value: 16.8, unit: "mmol/L", reference_range: "4.00-25.00", status: "unknown", category: "general" },
      { name: "ACR", value: 0.1, unit: "mg Alb/mmol", reference_range: "< 3.5", status: "unknown", category: "general" }
    ]
  };

  const session = buildSessionData({
    uploadId: "upload-1",
    parseResult,
    locale: "en"
  });
  const rendering = buildMarkerRenderingState({
    markers: session.markers,
    abnormalMarkers: session.abnormalMarkers
  });
  const referenceByName = new Map(rendering.markers.map((item) => [item.name, item.reference]));

  assert.equal(referenceByName.get("Sodium"), "135-145");
  assert.equal(referenceByName.get("Potassium"), "3.5-5.1");
  assert.equal(referenceByName.get("Chloride"), "95-110");
  assert.equal(referenceByName.get("Urea"), "3.0-10.0");
  assert.equal(referenceByName.get("Creatinine"), "44-110");
  assert.equal(referenceByName.get("Uric Acid"), "0.15-0.45");
  assert.equal(referenceByName.get("AST"), "< 41");
  assert.equal(referenceByName.get("ALT"), "< 51");
  assert.equal(referenceByName.get("Glucose"), "3.9 - 6.0");
  assert.equal(referenceByName.get("Urine Albumin"), "< 20.1");
  assert.equal(referenceByName.get("Urine Creatinine"), "4.00-25.00");
  assert.equal(referenceByName.get("ACR"), "< 3.5");
});
