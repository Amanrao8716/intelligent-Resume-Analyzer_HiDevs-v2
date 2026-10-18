"""Configuration management.

Settings come from (lowest to highest priority):
1. built-in defaults
2. a JSON config file (``--config`` or ``RESUME_ANALYZER_CONFIG``)
3. environment variables (``RESUME_ANALYZER_*``)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Dict, Optional

DEFAULT_WEIGHTS: Dict[str, float] = {
    "skills": 0.55,
    "experience": 0.25,
    "education": 0.10,
    "keywords": 0.10,
}


class ConfigError(ValueError):
    """Raised when configuration is invalid."""


@dataclass
class Config:
    weights: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    strong_threshold: float = 75.0
    maybe_threshold: float = 50.0
    output_dir: str = "output"
    log_level: str = "INFO"
    skills_file: Optional[str] = None  # custom taxonomy JSON

    def validate(self) -> "Config":
        if set(self.weights) != set(DEFAULT_WEIGHTS):
            raise ConfigError(f"weights must have keys {sorted(DEFAULT_WEIGHTS)}")
        if any(w < 0 for w in self.weights.values()):
            raise ConfigError("weights must be non-negative")
        total = sum(self.weights.values())
        if total <= 0:
            raise ConfigError("weights must sum to a positive number")
        self.weights = {k: v / total for k, v in self.weights.items()}
        if not 0 <= self.maybe_threshold <= self.strong_threshold <= 100:
            raise ConfigError("need 0 <= maybe_threshold <= strong_threshold <= 100")
        return self


def load_config(path: Optional[str] = None, env: Optional[dict] = None) -> Config:
    env = os.environ if env is None else env
    path = path or env.get("RESUME_ANALYZER_CONFIG")
    data: dict = {}
    if path:
        p = Path(path)
        if not p.is_file():
            raise ConfigError(f"config file not found: {p}")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"invalid JSON in {p}: {exc}") from exc

    valid = {f.name for f in fields(Config)}
    unknown = set(data) - valid
    if unknown:
        raise ConfigError(f"unknown config keys: {sorted(unknown)}")
    cfg = Config(**data)

    if "RESUME_ANALYZER_OUTPUT_DIR" in env:
        cfg.output_dir = env["RESUME_ANALYZER_OUTPUT_DIR"]
    if "RESUME_ANALYZER_LOG_LEVEL" in env:
        cfg.log_level = env["RESUME_ANALYZER_LOG_LEVEL"].upper()
    return cfg.validate()
