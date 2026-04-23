import importlib
import os
import sys
import types

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


class _QualityCompletions:
    def create(self, *, model: str, messages: list[dict[str, str]], temperature: float) -> _FakeCompletionResponse:
        prompt = messages[0]["content"]

        if "Required user-facing label for 'Overall status': Needs observation" in prompt and "Vitamin D is below reference." in prompt:
            return _FakeCompletionResponse(
                "Overall status:\n"
                "Needs observation\n\n"
                "Key observations:\n"
                "Main condition: Mild vitamin D and zinc deficiency.\n"
                "Short explanation: Vitamin D and zinc are below reference, while the CBC remains within range.\n\n"
                "What this means:\n"
                "This pattern is limited to mild nutritional abnormalities without evidence of a significant hematologic disorder.\n\n"
                "Next steps:\n"
                "Repeat vitamin D and zinc and review intake or supplementation with a clinician if needed.\n\n"
                "Final conclusion:\n"
                "Mild nutritional deviations are present; the blood count is otherwise stable.\n"
            )

        if "Required user-facing label for 'Overall status': Significant deviation" in prompt and "macrocytic anemia" in prompt.lower():
            return _FakeCompletionResponse(
                "Overall status:\n"
                "Significant deviation\n\n"
                "Key observations:\n"
                "Main condition: Severe macrocytic anemia.\n"
                "Short explanation: Hemoglobin is low, the red cell count is reduced, and MCV is elevated.\n\n"
                "What this means:\n"
                "This is a clinically important red-cell abnormality that requires prompt medical assessment.\n\n"
                "Next steps:\n"
                "Prompt medical evaluation is recommended, with repeat CBC and review for vitamin B12 or folate deficiency.\n\n"
                "Final conclusion:\n"
                "The overall picture is consistent with severe macrocytic anemia.\n"
            )

        return _FakeCompletionResponse(
            "Overall status:\n"
            "Normal\n\n"
            "Key observations:\n"
            "Main condition: No validated hematologic abnormality.\n"
            "Short explanation: Lymphocyte values remain within range, and reactive cell markers do not indicate a clinically meaningful white-cell disorder.\n\n"
            "What this means:\n"
            "The available results do not show a clinically meaningful blood-count disorder.\n\n"
            "Next steps:\n"
            "No urgent follow-up is required.\n\n"
            "Final conclusion:\n"
            "The laboratory picture is stable.\n"
        )


class _QualityChat:
    def __init__(self) -> None:
        self.completions = _QualityCompletions()


class _QualityClient:
    def __init__(self) -> None:
        self.chat = _QualityChat()


def _load_quality_analyze_module():
    os.environ["OPENAI_API_KEY"] = "test-key"
    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = lambda api_key=None: _QualityClient()
    fake_dotenv = types.ModuleType("dotenv")
    fake_dotenv.load_dotenv = lambda: None

    sys.modules.pop("interpreter.analyze", None)
    original_openai = sys.modules.get("openai")
    original_dotenv = sys.modules.get("dotenv")
    try:
        sys.modules["openai"] = fake_openai
        sys.modules["dotenv"] = fake_dotenv
        analyze = importlib.import_module("interpreter.analyze")
        analyze.client = _QualityClient()
        return analyze
    finally:
        if original_openai is None:
            sys.modules.pop("openai", None)
        else:
            sys.modules["openai"] = original_openai
        if original_dotenv is None:
            sys.modules.pop("dotenv", None)
        else:
            sys.modules["dotenv"] = original_dotenv


def test_mild_micronutrient_case_output_is_consistent_and_professional() -> None:
    _load_quality_analyze_module()
    result = api_services.execute_interpretation_flow(
        {
            "language": "en",
            "Hemoglobin": 145,
            "RBC": 4.8,
            "Hematocrit": 43,
            "Lymphocytes %": 32.7,
            "Lymphocytes abs.": 2.01,
            "WBC": 6.2,
            "Platelets": 250,
            "Vitamin D (25-OH)": 24,
            "Zinc": 8.8,
        }
    )

    interpretation = str(result["interpretation"]).lower()
    assert "needs observation" in interpretation
    assert "vitamin d" in interpretation
    assert "zinc" in interpretation
    assert "significant hematologic disorder" in interpretation
    assert "validated findings" not in interpretation
    assert "allowed claims" not in interpretation
    assert "guardrail" not in interpretation


def test_severe_macrocytic_anemia_output_remains_urgent_and_consistent() -> None:
    _load_quality_analyze_module()
    result = api_services.execute_interpretation_flow(
        {
            "language": "en",
            "Hemoglobin": 82,
            "RBC": 2.6,
            "Hematocrit": 26,
            "MCV": 108,
            "MCH": 35.2,
            "RDW": 16.8,
            "WBC": 6.1,
            "Platelets": 220,
        }
    )

    interpretation = str(result["interpretation"]).lower()
    assert "significant deviation" in interpretation
    assert "severe macrocytic anemia" in interpretation
    assert "prompt medical evaluation" in interpretation
    assert "validated findings" not in interpretation


def test_mixed_differential_output_stays_normal_and_avoids_false_lymphopenia() -> None:
    _load_quality_analyze_module()
    result = api_services.execute_interpretation_flow(
        {
            "language": "en",
            "RBC": 4.98,
            "NRBC": 0.0,
            "Lymphocytes %": 32.70,
            "Lymphocytes abs.": 2.01,
            "RE-LYMP abs": 0.08,
            "RE-LYMP %": 1.10,
            "AS-LYMP abs": 0.01,
            "AS-LYMP %": 0.40,
        }
    )

    interpretation = str(result["interpretation"]).lower()
    assert "normal" in interpretation
    assert "lymphopenia" not in interpretation
    assert "no validated hematologic abnormality" in interpretation
