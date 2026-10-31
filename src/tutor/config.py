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


def _load_dotenv(path: Path = ROOT / ".env") -> set[str]:
    """Sets the variables in .env that the shell has not set already, and returns their names.

    Blank values are skipped, so an empty `LLM_API_KEY=` never hides a key set in the shell.
    utf-8-sig also reads files that Windows editors save with a byte-order mark.
    """
    loaded: set[str] = set()
    if not path.exists():
        return loaded
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip().removeprefix("export ").strip(), value.strip()
        if value[:1] in ('"', "'"):
            value = value[1:].split(value[0], 1)[0]
        else:
            value = value.split(" #", 1)[0].strip()
        if value and key not in os.environ:
            os.environ[key] = value
            loaded.add(key)
    return loaded


DOTENV_KEYS = _load_dotenv()


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
