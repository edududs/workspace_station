from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from workspace.application.ports import SecretKeyPort

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(slots=True)
class FileSecretKeyStore(SecretKeyPort):
    key_path: Path

    def get_private_key_path(self) -> Path | None:
        if not self.key_path.exists():
            return None

        if self.key_path.stat().st_size == 0:
            return None

        return self.key_path
