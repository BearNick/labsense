import importlib
import os
import sys
import types
import unittest

sys.path.insert(0, "/opt/labsense/backend")


class _StubClient:
    def __init__(self) -> None:
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda **kwargs: None))


def _load_analyze_module():
    os.environ["OPENAI_API_KEY"] = "test-key"
    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = lambda api_key=None: _StubClient()
    fake_dotenv = types.ModuleType("dotenv")
    fake_dotenv.load_dotenv = lambda: None

    sys.modules.pop("interpreter.analyze", None)
    original_openai = sys.modules.get("openai")
    original_dotenv = sys.modules.get("dotenv")
    try:
        sys.modules["openai"] = fake_openai
        sys.modules["dotenv"] = fake_dotenv
        return importlib.import_module("interpreter.analyze")
    finally:
        if original_openai is None:
            sys.modules.pop("openai", None)
        else:
            sys.modules["openai"] = original_openai
        if original_dotenv is None:
            sys.modules.pop("dotenv", None)
        else:
            sys.modules["dotenv"] = original_dotenv


class InterpretationPromptLabelTests(unittest.TestCase):
    def test_build_prompt_keeps_english_inline_labels_for_english_reports(self) -> None:
        analyze = _load_analyze_module()
        prompt = analyze.build_prompt({"language": "en", "age": 30, "gender": "female", "Hemoglobin": 140})

        self.assertIn("'Main condition:'", prompt)
        self.assertIn("'Short explanation:'", prompt)
        self.assertIn("'Likely cause:'", prompt)
        self.assertNotIn("'Основное состояние:'", prompt)
        self.assertNotIn("'Condición principal:'", prompt)

    def test_build_prompt_uses_russian_inline_labels_for_russian_reports(self) -> None:
        analyze = _load_analyze_module()
        prompt = analyze.build_prompt({"language": "ru", "age": 30, "gender": "female", "Гемоглобин": 140})

        self.assertIn("'Основное состояние:'", prompt)
        self.assertIn("'Краткое объяснение:'", prompt)
        self.assertIn("'Вероятная причина:'", prompt)
        self.assertNotIn("'Main condition:'", prompt)
        self.assertNotIn("'Short explanation:'", prompt)
        self.assertNotIn("'Likely cause:'", prompt)

    def test_build_prompt_uses_spanish_inline_labels_for_spanish_reports(self) -> None:
        analyze = _load_analyze_module()
        prompt = analyze.build_prompt({"language": "es", "age": 30, "gender": "female", "Hemoglobina": 140})

        self.assertIn("'Condición principal:'", prompt)
        self.assertIn("'Explicación breve:'", prompt)
        self.assertIn("'Causa probable:'", prompt)
        self.assertNotIn("'Main condition:'", prompt)
        self.assertNotIn("'Short explanation:'", prompt)
        self.assertNotIn("'Likely cause:'", prompt)


if __name__ == "__main__":
    unittest.main()
