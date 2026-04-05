from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProjectDefinition:
    name: str
    url: str


@dataclass(frozen=True, slots=True)
class ManagedRepository:
    name: str
    path: Path
    exists: bool
    configured_url: str | None = None

    @property
    def state(self) -> str:
        return "present" if self.exists else "missing"
