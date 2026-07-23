from __future__ import annotations

import traceback

from core.command_registry import command_registry


class DesktopApi:
    def invoke(self, command: str, payload: dict | None = None) -> dict:
        try:
            result = command_registry.invoke(command, payload)

            return {
                "ok": True,
                "result": result,
            }
        except Exception as exc:
            traceback.print_exc()

            return {
                "ok": False,
                "error": str(exc),
            }
