import importlib.util
import pathlib
import sys
import unittest


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "check_llm_keys.py"
SPEC = importlib.util.spec_from_file_location("check_llm_keys", SCRIPT_PATH)
check_llm_keys = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_llm_keys
SPEC.loader.exec_module(check_llm_keys)


class CheckLlmKeysTests(unittest.TestCase):
    def test_selects_configured_provider_when_requested(self):
        env = {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-test",
            "GEMINI_API_KEY": "gemini-test",
        }

        self.assertEqual(check_llm_keys.select_providers(env, "configured"), ["openai"])

    def test_selects_only_providers_with_keys_for_all(self):
        env = {
            "OPENAI_API_KEY": "sk-test",
            "GEMINI_API_KEY": "your_gemini_api_key_here",
        }

        self.assertEqual(check_llm_keys.select_providers(env, "all"), ["openai"])

    def test_placeholder_keys_are_not_configured(self):
        env = {"GEMINI_API_KEY": "your_gemini_api_key_here"}

        result = check_llm_keys.provider_config(env, "gemini")

        self.assertFalse(result.configured)
        self.assertEqual(result.reason, "GEMINI_API_KEY is missing or still a placeholder")

    def test_openai_config_reads_base_url_and_organization(self):
        env = {
            "OPENAI_API_KEY": "sk-test",
            "OPENAI_MODEL": "gpt-test",
            "OPENAI_BASE_URL": "http://example.test/v1",
            "OPENAI_ORGANIZATION": "org-test",
        }

        result = check_llm_keys.provider_config(env, "openai")

        self.assertTrue(result.configured)
        self.assertEqual(result.model, "gpt-test")
        self.assertEqual(result.base_url, "http://example.test/v1")
        self.assertEqual(result.organization, "org-test")

    def test_gemini_config_reads_base_url(self):
        env = {
            "GEMINI_API_KEY": "gemini-test",
            "GEMINI_MODEL": "gemini-test-model",
            "GEMINI_BASE_URL": "http://example.test",
        }

        result = check_llm_keys.provider_config(env, "gemini")

        self.assertTrue(result.configured)
        self.assertEqual(result.model, "gemini-test-model")
        self.assertEqual(result.base_url, "http://example.test/v1beta/openai/")

    def test_exit_code_fails_when_any_provider_fails(self):
        results = [
            check_llm_keys.CheckResult("gemini", True, "ok"),
            check_llm_keys.CheckResult("openai", False, "bad key"),
        ]

        self.assertEqual(check_llm_keys.exit_code_for(results), 1)

    def test_exit_code_passes_when_all_requested_providers_pass(self):
        results = [
            check_llm_keys.CheckResult("gemini", True, "ok"),
            check_llm_keys.CheckResult("openai", True, "ok"),
        ]

        self.assertEqual(check_llm_keys.exit_code_for(results), 0)

    def test_models_url_uses_provider_base_url(self):
        openai = check_llm_keys.ProviderConfig(
            provider="openai",
            configured=True,
            api_key="sk-test",
            model="gpt-test",
            base_url="http://example.test/v1",
            organization="org-test",
        )
        gemini = check_llm_keys.ProviderConfig(
            provider="gemini",
            configured=True,
            api_key="gemini-test",
            model="gemini-test",
            base_url="http://example.test/v1beta/openai/",
        )

        self.assertEqual(check_llm_keys.models_url(openai), "http://example.test/v1/models")
        self.assertEqual(check_llm_keys.models_url(gemini), "http://example.test/v1beta/openai/models")

    def test_official_openai_models_url_when_base_url_is_empty(self):
        config = check_llm_keys.ProviderConfig(
            provider="openai",
            configured=True,
            api_key="sk-test",
            model="gpt-test",
            base_url="",
        )

        self.assertEqual(check_llm_keys.models_url(config), "https://api.openai.com/v1/models")


if __name__ == "__main__":
    unittest.main()
