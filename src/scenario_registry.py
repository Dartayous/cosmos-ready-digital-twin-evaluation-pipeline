from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class ScenarioRegistry:
    """Loads and serves scenario definitions for Project 08."""

    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)
        self._data = self._load_json()

    def _load_json(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Scenario config not found: {self.config_path}"
            )

        with self.config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if "scenarios" not in data:
            raise ValueError("Scenario config must contain a 'scenarios' list.")

        return data

    @property
    def project(self) -> str:
        return self._data.get("project", "unknown_project")

    @property
    def version(self) -> str:
        return self._data.get("version", "unknown_version")

    @property
    def scenarios(self) -> list[Dict[str, Any]]:
        return self._data["scenarios"]

    def get_scenario(self, scenario_id: str) -> Dict[str, Any]:
        for scenario in self.scenarios:
            if scenario["scenario_id"] == scenario_id:
                return scenario

        raise KeyError(f"Scenario not found: {scenario_id}")


if __name__ == "__main__":
    registry = ScenarioRegistry("configs/scenarios.json")
    print(f"Project: {registry.project}")
    print(f"Version: {registry.version}")
    print("Scenarios:")
    for scenario in registry.scenarios:
        print(f"  - {scenario['scenario_id']}: {scenario['description']}")