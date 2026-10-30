"""Paths and settings shared by every POC component."""
from __future__ import annotations

import hashlib
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "app.toml"
CONTENT_DIR = ROOT / "content" / "poc"
EVAL_DIR = ROOT / "eval" / "poc"
VAR_DIR = Path(os.environ.get("TUTOR_VAR_DIR", ROOT / "var"))


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    raw: dict
    sha256: str

    @property
    def dataset_build(self) -> Path:
        return ROOT / self.raw["dataset"]["build"]

    @property
    def llm(self) -> dict:
        return self.raw["llm"]

    @property
    def learner_model(self) -> dict:
        return self.raw["learner_model"]

    @property
    def budgets(self) -> dict:
        return self.raw["budgets"]

    @property
    def poc(self) -> dict:
        return self.raw["poc"]


def load_settings() -> Settings:
    data = CONFIG_PATH.read_bytes()
    return Settings(raw=tomllib.loads(data.decode("utf-8")), sha256=hashlib.sha256(data).hexdigest())


SETTINGS = load_settings()


def db_path(name: str = "tutor.db") -> Path:
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    return VAR_DIR / name
