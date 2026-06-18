import json
import os
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = REPO_ROOT / "scenarios"
VALID_SCENARIOS = frozenset({"ecommerce", "healthcare", "banking"})


def normalize_scenario(value: str | None) -> str:
    scenario = (value or "ecommerce").strip().lower()
    if scenario not in VALID_SCENARIOS:
        raise ValueError(f"Invalid scenario '{value}'. Use one of: {', '.join(sorted(VALID_SCENARIOS))}")
    return scenario


def resolve_scenario(explicit: str | None = None) -> str:
    return normalize_scenario(explicit or os.environ.get("AZURE_ENV_SCENARIO") or os.environ.get("DEPLOYMENT_SCENARIO"))


def scenario_dir(scenario: str | None = None) -> Path:
    return SCENARIOS_DIR / resolve_scenario(scenario)


def load_manifest(scenario: str | None = None) -> dict[str, Any]:
    path = scenario_dir(scenario) / "manifest.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_agent_instructions(scenario: str | None, name: str) -> str:
    path = scenario_dir(scenario) / "agents" / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


def catalog_csv_path(scenario: str | None = None) -> Path:
    manifest = load_manifest(scenario)
    rel = manifest.get("data", {}).get("catalogCsv", "data/catalog.csv")
    return scenario_dir(scenario) / rel


def policies_dir(scenario: str | None = None) -> Path:
    manifest = load_manifest(scenario)
    rel = manifest.get("data", {}).get("policiesDir", "data/policies")
    return scenario_dir(scenario) / rel


def catalog_tool_name(scenario: str | None = None) -> str:
    manifest = load_manifest(scenario)
    name = manifest.get("agents", {}).get("catalogToolName")
    if name:
        return str(name)
    sid = resolve_scenario(scenario)
    return {
        "ecommerce": "product_agent",
        "healthcare": "services_agent",
        "banking": "accounts_agent",
    }[sid]


def policy_tool_name(scenario: str | None = None) -> str:
    manifest = load_manifest(scenario)
    name = manifest.get("agents", {}).get("policyToolName")
    if name:
        return str(name)
    sid = resolve_scenario(scenario)
    return {
        "ecommerce": "policy_agent",
        "healthcare": "care_policy_agent",
        "banking": "banking_policy_agent",
    }[sid]
