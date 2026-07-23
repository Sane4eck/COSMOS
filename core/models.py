from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from fastapi import APIRouter


CommandHandler = Callable[[dict], dict]


@dataclass(frozen=True)
class AppDefinition:
    app_id: str
    title: str
    frontend_dir: Path
    commands: dict[str, CommandHandler]
    router: APIRouter | None = None

    @property
    def frontend_url(self) -> str:
        return f"/apps/{self.app_id}/index.html"
