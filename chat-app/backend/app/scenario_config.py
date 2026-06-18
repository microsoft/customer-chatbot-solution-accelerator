import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

VALID_SCENARIOS = frozenset({"ecommerce", "healthcare", "banking"})


def _resolve_scenarios_dir() -> Path:
    env_dir = os.environ.get("SCENARIOS_DIR", "").strip()
    if env_dir:
        return Path(env_dir)
    here = Path(__file__).resolve().parent
    for root in [here, *here.parents]:
        candidate = root / "scenarios"
        if candidate.is_dir():
            return candidate
    return here.parent / "scenarios"


SCENARIOS_DIR = _resolve_scenarios_dir()


def normalize_scenario(value: str | None) -> str:
    scenario = (value or "ecommerce").strip().lower()
    if scenario not in VALID_SCENARIOS:
        return "ecommerce"
    return scenario


def current_scenario() -> str:
    return normalize_scenario(
        os.environ.get("DEPLOYMENT_SCENARIO") or os.environ.get("AZURE_ENV_SCENARIO")
    )


_CATALOG_TOOL_NAMES = {
    "ecommerce": "product_agent",
    "healthcare": "services_agent",
    "banking": "accounts_agent",
}

_POLICY_TOOL_NAMES = {
    "ecommerce": "policy_agent",
    "healthcare": "care_policy_agent",
    "banking": "banking_policy_agent",
}


def catalog_tool_name(scenario: str | None = None) -> str:
    env = os.environ.get("FOUNDRY_CATALOG_TOOL_NAME", "").strip()
    if env:
        return env
    manifest = load_manifest(scenario)
    name = manifest.get("agents", {}).get("catalogToolName")
    if name:
        return str(name)
    sid = normalize_scenario(scenario or current_scenario())
    return _CATALOG_TOOL_NAMES[sid]


def policy_tool_name(scenario: str | None = None) -> str:
    env = os.environ.get("FOUNDRY_POLICY_TOOL_NAME", "").strip()
    if env:
        return env
    manifest = load_manifest(scenario)
    name = manifest.get("agents", {}).get("policyToolName")
    if name:
        return str(name)
    sid = normalize_scenario(scenario or current_scenario())
    return _POLICY_TOOL_NAMES[sid]


@lru_cache(maxsize=4)
def load_manifest(scenario: str | None = None) -> dict[str, Any]:
    sid = normalize_scenario(scenario or current_scenario())
    path = SCENARIOS_DIR / sid / "manifest.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def welcome_config() -> dict[str, str]:
    env_title = os.environ.get("CHAT_WELCOME_TITLE", "").strip()
    env_subtitle = os.environ.get("CHAT_WELCOME_SUBTITLE", "").strip()
    manifest = load_manifest()
    welcome = manifest.get("welcome", {})
    return {
        "title": env_title or welcome.get("title", "Hey! I'm here to help."),
        "subtitle": env_subtitle or welcome.get("subtitle", "Ask a question to get started."),
        "hint": welcome.get("hint", "Click the new chat button above to start a new chat anytime"),
    }


def compliance_banner() -> str:
    manifest = load_manifest()
    return manifest.get("host", {}).get("complianceBanner", "")
