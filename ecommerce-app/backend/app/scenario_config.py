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


@lru_cache(maxsize=4)
def load_manifest(scenario: str | None = None) -> dict[str, Any]:
    sid = normalize_scenario(scenario or current_scenario())
    path = SCENARIOS_DIR / sid / "manifest.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def host_config() -> dict[str, Any]:
    manifest = load_manifest()
    host = manifest.get("host", {})
    return {
        "appTitle": os.environ.get("VITE_HOST_APP_TITLE") or host.get("appTitle", "Contoso"),
        "iconPath": host.get("iconPath", "/contoso-icon.png"),
        "widgetTheme": os.environ.get("VITE_CHAT_WIDGET_THEME") or host.get("widgetTheme", "dark"),
        "complianceBanner": host.get("complianceBanner", ""),
    }
