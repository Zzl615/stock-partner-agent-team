#!/usr/bin/env python3
"""Check whether configured Gemini/OpenAI API keys can make a minimal request."""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from dataclasses import dataclass
from typing import Callable

import requests
from dotenv import load_dotenv


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
PLACEHOLDER_PREFIXES = ("your_", "YOUR_")
SUPPORTED_PROVIDERS = ("gemini", "openai")


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    configured: bool
    api_key: str
    model: str
    base_url: str
    organization: str = ""
    reason: str = ""


@dataclass(frozen=True)
class CheckResult:
    provider: str
    ok: bool
    message: str


def is_real_value(value: str | None) -> bool:
    if not value:
        return False
    stripped = value.strip()
    return bool(stripped) and not stripped.startswith(PLACEHOLDER_PREFIXES)


def provider_config(env: dict[str, str], provider: str) -> ProviderConfig:
    if provider == "gemini":
        api_key_name = "GEMINI_API_KEY"
        model_name = "GEMINI_MODEL"
        default_model = "gemini-1.5-pro"
        base_url = env.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/").strip()
        if base_url and not base_url.rstrip("/").endswith("/openai"):
            base_url = base_url.rstrip("/") + "/v1beta/openai/"
    elif provider == "openai":
        api_key_name = "OPENAI_API_KEY"
        model_name = "OPENAI_MODEL"
        default_model = "gpt-4o"
        base_url = env.get("OPENAI_BASE_URL", "").strip()
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    api_key = env.get(api_key_name, "").strip()
    model = env.get(model_name, default_model).strip() or default_model
    organization = env.get("OPENAI_ORGANIZATION", "").strip() if provider == "openai" else ""
    if not is_real_value(api_key):
        return ProviderConfig(
            provider=provider,
            configured=False,
            api_key="",
            model=model,
            base_url=base_url,
            organization=organization,
            reason=f"{api_key_name} is missing or still a placeholder",
        )

    return ProviderConfig(
        provider=provider,
        configured=True,
        api_key=api_key,
        model=model,
        base_url=base_url,
        organization=organization,
    )


def select_providers(env: dict[str, str], requested: str) -> list[str]:
    if requested in SUPPORTED_PROVIDERS:
        return [requested]

    if requested == "configured":
        configured = env.get("LLM_PROVIDER", "gemini").strip().lower()
        if configured not in SUPPORTED_PROVIDERS:
            return []
        return [configured]

    providers = []
    for provider in SUPPORTED_PROVIDERS:
        if provider_config(env, provider).configured:
            providers.append(provider)
    return providers


def check_openai(config: ProviderConfig, timeout: float) -> CheckResult:
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url or None,
            organization=config.organization or None,
            timeout=timeout,
        )
        response = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": "Reply with OK."}],
            max_tokens=3,
        )
        content = response.choices[0].message.content or ""
        return CheckResult(config.provider, True, f"valid; model responded: {content.strip()[:20]}")
    except Exception as exc:
        return CheckResult(config.provider, False, str(exc))


def check_gemini(config: ProviderConfig, timeout: float) -> CheckResult:
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=timeout,
        )
        response = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": "Reply with OK."}],
            max_tokens=3,
        )
        content = response.choices[0].message.content or ""
        return CheckResult(config.provider, True, f"valid; model responded: {content.strip()[:20]}")
    except Exception as exc:
        return CheckResult(config.provider, False, str(exc))


def check_provider(config: ProviderConfig, timeout: float) -> CheckResult:
    if not config.configured:
        return CheckResult(config.provider, False, config.reason)
    checks: dict[str, Callable[[ProviderConfig, float], CheckResult]] = {
        "gemini": check_gemini,
        "openai": check_openai,
    }
    return checks[config.provider](config, timeout)


def models_url(config: ProviderConfig) -> str:
    if config.base_url:
        return config.base_url.rstrip("/") + "/models"
    return "https://api.openai.com/v1/models"


def check_models_endpoint(config: ProviderConfig, timeout: float) -> CheckResult:
    if not config.configured:
        return CheckResult(config.provider, False, config.reason)

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    if config.organization:
        headers["OpenAI-Organization"] = config.organization

    try:
        response = requests.get(models_url(config), headers=headers, timeout=timeout)
        if response.status_code != 200:
            return CheckResult(config.provider, False, f"HTTP {response.status_code}: {response.text[:300]}")
        data = response.json()
        models = data.get("data", [])
        preview = ", ".join(str(model.get("id", "")) for model in models[:5])
        return CheckResult(config.provider, True, f"valid; visible models: {len(models)}; first: {preview}")
    except Exception as exc:
        return CheckResult(config.provider, False, str(exc))


def exit_code_for(results: list[CheckResult]) -> int:
    return 0 if results and all(result.ok for result in results) else 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Gemini/OpenAI API keys from .env.")
    parser.add_argument(
        "--provider",
        choices=("configured", "all", "gemini", "openai"),
        default="configured",
        help="Provider to check. Default checks LLM_PROVIDER from .env.",
    )
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_PATH),
        help="Path to .env file. Defaults to project .env.",
    )
    parser.add_argument("--timeout", type=float, default=20.0, help="Request timeout in seconds.")
    parser.add_argument(
        "--mode",
        choices=("models", "chat"),
        default="models",
        help="Validation mode. models checks GET /models; chat sends a minimal chat completion.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    env_file = pathlib.Path(args.env_file)
    if env_file.exists():
        load_dotenv(env_file, override=False)
    else:
        print(f"[!] Env file not found: {env_file}")

    env = dict(os.environ)
    providers = select_providers(env, args.provider)
    if not providers:
        print("[x] No supported provider selected. Set LLM_PROVIDER to gemini/openai or use --provider.")
        return 1

    results = []
    for provider in providers:
        config = provider_config(env, provider)
        if args.mode == "chat":
            print(f"[*] Checking {provider} chat with model {config.model}...")
            result = check_provider(config, args.timeout)
        else:
            print(f"[*] Checking {provider} models endpoint...")
            result = check_models_endpoint(config, args.timeout)
        results.append(result)
        marker = "ok" if result.ok else "failed"
        print(f"[{marker}] {provider}: {result.message}")

    return exit_code_for(results)


if __name__ == "__main__":
    raise SystemExit(main())
