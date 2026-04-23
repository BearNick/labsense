import sys
import unittest

sys.path.insert(0, "/opt/labsense")
sys.path.insert(0, "/opt/labsense/backend")

from tests.pipeline_diagnostic import build_diagnostic_fixtures, first_divergence_layer, trace_pipeline


class PipelineDiagnosticTests(unittest.TestCase):
    maxDiff = None

    def test_synthetic_fixtures_match_expected_layers(self) -> None:
        for fixture in build_diagnostic_fixtures():
            with self.subTest(fixture=fixture.name):
                trace = trace_pipeline(fixture)
                divergence = first_divergence_layer(fixture, trace)
                if divergence is not None:
                    self.fail(
                        f"{fixture.name} diverged first at {divergence}\n"
                        f"trace:\n{trace.to_pretty_json()}"
                    )

    def test_first_failing_layer_is_final_response_when_model_invents_lymphopenia(self) -> None:
        for fixture_name in ("cbc_normal_panel", "cbc_vitamin_d_zinc"):
            fixture = next(item for item in build_diagnostic_fixtures() if item.name == fixture_name)
            trace = trace_pipeline(fixture, apply_consistency_guard=False, force_inconsistent_model=True)
            divergence = first_divergence_layer(fixture, trace)

            self.assertEqual(
                divergence,
                "final_interpretation_response",
                msg=f"unexpected divergence for {fixture_name}\n{trace.to_pretty_json()}",
            )
            self.assertTrue(trace.final_response["consistency_issues"], msg=trace.to_pretty_json())

    def test_traces_include_every_required_layer(self) -> None:
        fixture = next(item for item in build_diagnostic_fixtures() if item.name == "cbc_vitamin_d_zinc")
        trace = trace_pipeline(fixture)

        self.assertIn("Vitamin D (25-OH)", trace.raw_values)
        self.assertIn("Vitamin D (25-OH)", trace.merged_values)
        self.assertIn("Витамин D (25-OH)", trace.payload)
        self.assertEqual(trace.abnormal_markers, ["Витамин D (25-OH)", "Цинк"])
        self.assertEqual(trace.risk_status["priority_notes"], ["Витамин D (25-OH) ниже референса.", "Цинк ниже референса."])
        self.assertIn("interpretation", trace.final_response)

    def test_rbc_never_equals_nrbc(self) -> None:
        fixture = next(item for item in build_diagnostic_fixtures() if item.name == "cbc_distinct_special_markers")
        trace = trace_pipeline(fixture)

        self.assertNotEqual(trace.payload["Эритроциты"], trace.payload["NRBC"])

    def test_lymphocyte_percent_never_equals_absolute_variants(self) -> None:
        fixture = next(item for item in build_diagnostic_fixtures() if item.name == "cbc_distinct_special_markers")
        trace = trace_pipeline(fixture)

        self.assertNotEqual(trace.payload["Лимфоциты %"], trace.payload["Лимфоциты абс."])
        self.assertNotEqual(trace.payload["Лимфоциты %"], trace.payload["RE-LYMP abs"])
        self.assertNotEqual(trace.payload["Лимфоциты %"], trace.payload["AS-LYMP abs"])

    def test_percentage_markers_never_replace_absolute_markers(self) -> None:
        fixture = next(item for item in build_diagnostic_fixtures() if item.name == "cbc_distinct_special_markers")
        trace = trace_pipeline(fixture)

        self.assertEqual(trace.payload["Лимфоциты %"], 32.70)
        self.assertEqual(trace.payload["RE-LYMP %"], 1.10)
        self.assertEqual(trace.payload["AS-LYMP %"], 0.40)
        self.assertEqual(trace.payload["Лимфоциты абс."], 2.01)
        self.assertEqual(trace.payload["RE-LYMP abs"], 0.08)
        self.assertEqual(trace.payload["AS-LYMP abs"], 0.01)

    def test_extracted_valid_markers_do_not_disappear_downstream(self) -> None:
        fixture = next(item for item in build_diagnostic_fixtures() if item.name == "cbc_distinct_special_markers")
        trace = trace_pipeline(fixture)

        for marker in ("NRBC", "RE-LYMP abs", "RE-LYMP %", "AS-LYMP abs", "AS-LYMP %"):
            self.assertIn(marker, trace.raw_values)
        for marker in ("NRBC", "RE-LYMP abs", "RE-LYMP %", "AS-LYMP abs", "AS-LYMP %"):
            self.assertIn(marker, trace.payload)

    def test_downstream_layers_do_not_invent_abnormalities_absent_in_payload(self) -> None:
        fixture = next(item for item in build_diagnostic_fixtures() if item.name == "cbc_vitamin_d_zinc")
        trace = trace_pipeline(fixture)

        self.assertNotIn("Лимфоциты % ниже референса.", trace.prompt)
        self.assertNotIn("лимфопени", trace.final_response["interpretation"].lower())
        self.assertNotIn("significant abnormality", trace.final_response["interpretation"].lower())

    def test_normal_payload_lymphocyte_percent_cannot_produce_lymphopenia(self) -> None:
        fixture = next(item for item in build_diagnostic_fixtures() if item.name == "cbc_normal_panel")
        trace = trace_pipeline(fixture)

        self.assertEqual(trace.payload["Лимфоциты %"], 32.70)
        self.assertNotIn("лимфопени", trace.final_response["interpretation"].lower())
        self.assertNotIn("lymphopen", trace.final_response["interpretation"].lower())

    def test_mild_vitamin_d_and_zinc_case_cannot_become_significant_due_to_lymphocytes(self) -> None:
        fixture = next(item for item in build_diagnostic_fixtures() if item.name == "cbc_vitamin_d_zinc")
        trace = trace_pipeline(fixture)

        self.assertEqual(trace.risk_status["color_key"], "yellow")
        self.assertEqual(trace.abnormal_markers, ["Витамин D (25-OH)", "Цинк"])
        self.assertNotIn("лимфопени", trace.final_response["interpretation"].lower())
        self.assertNotIn("значимое отклонение", trace.final_response["interpretation"].lower())

    def test_final_prose_agrees_with_abnormal_marker_list(self) -> None:
        fixture = next(item for item in build_diagnostic_fixtures() if item.name == "cbc_vitamin_d_zinc")
        trace = trace_pipeline(fixture)
        interpretation = trace.final_response["interpretation"].lower()

        self.assertTrue("витамин d" in interpretation or "vitamin d" in interpretation)
        self.assertTrue("цинк" in interpretation or "zinc" in interpretation)
        self.assertNotIn("lymphopen", interpretation)
        self.assertNotIn("лимфопени", interpretation)
        self.assertNotIn("допустимые выводы ограничены", interpretation)
        self.assertNotIn("финальный текст ограничен подтвержденными находками", interpretation)
        self.assertNotIn("allowed claims are limited", interpretation)
        self.assertNotIn("final prose is constrained", interpretation)


if __name__ == "__main__":
    unittest.main()
