from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class Scope:
    grade: int
    subject: str
    book: str | None = None
    unit: int | None = None


class KnowledgePort(Protocol):
    dataset_id: str
    def catalogue(self) -> list[dict]: ...
    def search(self, query: str, scope: Scope, limit: int=3) -> list[dict]: ...
    def passage(self, passage_id: str) -> dict | None: ...
    def nodes(self, scope: Scope) -> list[dict]: ...


class SafetyScreenPort(Protocol):
    def __call__(self, latest: str, previous: str | None) -> Literal["crisis", "injection"] | None: ...


class LanguagePort(Protocol):
    def generate(self, system: str, context: dict) -> str: ...
