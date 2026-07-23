from __future__ import annotations

from threading import RLock
from typing import Callable


CommandHandler = Callable[[dict], dict]


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, CommandHandler] = {}
        self._lock = RLock()

    def register(self, name: str, handler: CommandHandler) -> None:
        with self._lock:
            if name in self._commands:
                raise ValueError(f"Команда вже зареєстрована: {name}")

            self._commands[name] = handler

    def invoke(self, name: str, payload: dict | None = None) -> dict:
        with self._lock:
            handler = self._commands.get(name)

        if handler is None:
            raise KeyError(f"Невідома команда: {name}")

        return handler(payload or {})


command_registry = CommandRegistry()
