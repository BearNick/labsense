import importlib
import os
import sys
import types
import unittest

sys.path.insert(0, "/opt/labsense")
sys.path.insert(0, "/opt/labsense/backend")

fastapi_stub = types.ModuleType("fastapi")


class _HTTPException(Exception):
    def __init__(self, status_code=None, detail=None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _UploadFile:
    pass


fastapi_stub.HTTPException = _HTTPException
fastapi_stub.UploadFile = _UploadFile
sys.modules.setdefault("fastapi", fastapi_stub)

import api.services as api_services


class _FakeCompletionResponse:
    def __init__(self, content: str) -> None:
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=content))]


class _PromptDrivenCompletions:
    def create(self, *, model: str, messages: list[dict[str, str]], temperature: float) -> _FakeCompletionResponse:
        prompt = messages[0]["content"]
        if "STRICT CONSISTENCY RULE:" not in prompt:
            content = (
                "Overall status:\n"
                "Significant deviation\n\n"
                "Key observations:\n"
                "Main condition: Lymphopenia.\n"
                "Short explanation: Lymphocytes % are below reference.\n\n"
                "What this means:\n"
                "This suggests a significant white-cell abnormality.\n\n"
                "Next steps:\n"
                "Medical evaluation recommended.\n\n"
                "Final conclusion:\n"
                "Significant abnormality.\n"
            )
            return _FakeCompletionResponse(content)

        if "Цинк ниже референса." not in prompt:
            raise AssertionError("Prompt did not preserve zinc as a detected deviation.")
        if "Лимфоциты % ниже референса." in prompt:
            raise AssertionError("Prompt incorrectly marked lymphocytes % as abnormal.")

        content = (
            "Overall status:\n"
            "Needs observation\n\n"
            "Key observations:\n"
            "Main condition: Mild vitamin D insufficiency.\n"
            "Short explanation: Vitamin D is below reference.\n"
            "Secondary observations: Zinc is also below reference, while lymphocyte values remain within range.\n\n"
            "What this means:\n"
            "The overall picture is otherwise stable, with limited nutritional deviations rather than a significant blood-cell abnormality.\n\n"
            "Next steps:\n"
            "Repeat vitamin D and zinc, and review supplementation with a clinician if symptoms or low intake are present.\n\n"
            "Final conclusion:\n"
            "Borderline nutritional deviations without evidence of lymphopenia.\n"
        )
        return _FakeCompletionResponse(content)


class _InconsistentPromptDrivenCompletions:
    def create(self, *, model: str, messages: list[dict[str, str]], temperature: float) -> _FakeCompletionResponse:
        return _FakeCompletionResponse(
            "Overall status:\n"
            "Significant deviation\n\n"
            "Key observations:\n"
            "Main condition: Lymphopenia.\n"
            "Short explanation: Lymphocytes % are below reference.\n\n"
            "What this means:\n"
            "This suggests a significant white-cell abnormality.\n\n"
            "Next steps:\n"
            "Medical evaluation recommended.\n\n"
            "Final conclusion:\n"
            "Significant abnormality.\n"
        )


class _PromptDrivenChat:
    def __init__(self) -> None:
        self.completions = _PromptDrivenCompletions()


class _PromptDrivenClient:
    def __init__(self) -> None:
        self.chat = _PromptDrivenChat()


class _InconsistentPromptDrivenChat:
    def __init__(self) -> None:
        self.completions = _InconsistentPromptDrivenCompletions()


class _InconsistentPromptDrivenClient:
    def __init__(self) -> None:
        self.chat = _InconsistentPromptDrivenChat()


def _load_analyze_module():
    os.environ["OPENAI_API_KEY"] = "test-key"
    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = lambda api_key=None: _PromptDrivenClient()
    fake_dotenv = types.ModuleType("dotenv")
    fake_dotenv.load_dotenv = lambda: None

    sys.modules.pop("interpreter.analyze", None)
    with_test_modules = {"openai": fake_openai, "dotenv": fake_dotenv}
    original_modules = {name: sys.modules.get(name) for name in with_test_modules}
    try:
        sys.modules.update(with_test_modules)
        analyze = importlib.import_module("interpreter.analyze")
        analyze.client = _PromptDrivenClient()
        return analyze
    finally:
        for name, module in original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def _load_inconsistent_analyze_module():
    os.environ["OPENAI_API_KEY"] = "test-key"
    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = lambda api_key=None: _InconsistentPromptDrivenClient()
    fake_dotenv = types.ModuleType("dotenv")
    fake_dotenv.load_dotenv = lambda: None

    sys.modules.pop("interpreter.analyze", None)
    with_test_modules = {"openai": fake_openai, "dotenv": fake_dotenv}
    original_modules = {name: sys.modules.get(name) for name in with_test_modules}
    try:
        sys.modules.update(with_test_modules)
        analyze = importlib.import_module("interpreter.analyze")
        analyze.client = _InconsistentPromptDrivenClient()
        return analyze
    finally:
        for name, module in original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class FinalInterpretation123PdfTests(unittest.TestCase):
    def test_123_pdf_final_output_stays_consistent_with_normalized_payload(self) -> None:
        _load_analyze_module()
        payload = {
            "age": 30,
            "gender": "female",
            "language": "ru",
            "Эритроциты": 4.98,
            "Лимфоциты %": 32.70,
            "Лимфоциты абс.": 2.01,
            "Витамин D (25-OH)": 29,
            "Цинк": 8.5,
            "RE-LYMP abs": 0.08,
            "RE-LYMP %": 1.10,
        }
        parse_context = {
            "extracted_count": 7,
            "confidence_score": 100,
            "confidence_level": "high",
            "confidence_explanation": "golden 123.pdf payload",
            "reference_coverage": 1.0,
            "unit_coverage": 1.0,
            "structural_consistency": 1.0,
            "fallback_used": False,
            "warnings": [],
            "source": "text",
        }

        result = api_services.execute_interpretation_flow(payload, parse_context)

        interpretation = str(result["interpretation"]).lower()
        risk_status = result["risk_status"]
        plan = result["plan"]

        self.assertIsNotNone(risk_status)
        self.assertEqual(risk_status["label"], "Нужно наблюдение")
        self.assertEqual(risk_status["color_key"], "yellow")
        self.assertIn("Витамин D (25-OH) ниже референса.", risk_status["priority_notes"])
        self.assertIn("Цинк ниже референса.", risk_status["priority_notes"])
        self.assertNotIn("лимфопени", interpretation)
        self.assertNotIn("лимфоциты % ниже референса", interpretation)
        self.assertTrue("vitamin d" in interpretation or "витамин d" in interpretation)
        self.assertTrue("цинк" in interpretation or "zinc" in interpretation)
        self.assertNotIn("significant abnormality", interpretation)
        self.assertNotIn("значимое отклонение", interpretation)
        self.assertEqual(plan.status_label, "")

    def test_123_pdf_inconsistent_model_output_is_replaced_at_final_layer(self) -> None:
        _load_inconsistent_analyze_module()
        payload = {
            "age": 30,
            "gender": "female",
            "language": "ru",
            "Эритроциты": 4.98,
            "Лимфоциты %": 32.70,
            "Лимфоциты абс.": 2.01,
            "Витамин D (25-OH)": 29,
            "Цинк": 8.5,
            "RE-LYMP abs": 0.08,
            "RE-LYMP %": 1.10,
        }
        parse_context = {
            "extracted_count": 7,
            "confidence_score": 100,
            "confidence_level": "high",
            "confidence_explanation": "golden 123.pdf payload",
            "reference_coverage": 1.0,
            "unit_coverage": 1.0,
            "structural_consistency": 1.0,
            "fallback_used": False,
            "warnings": [],
            "source": "text",
        }

        result = api_services.execute_interpretation_flow(payload, parse_context)

        interpretation = str(result["interpretation"]).lower()

        self.assertTrue(result["consistency_issues"])
        self.assertIn("витамин d", interpretation)
        self.assertIn("цинк", interpretation)
        self.assertNotIn("лимфопени", interpretation)
        self.assertNotIn("significant abnormality", interpretation)


if __name__ == "__main__":
    unittest.main()
