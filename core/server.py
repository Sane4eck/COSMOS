from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from apps.registry import APPS
from core.command_registry import command_registry
from core.paths import resource_path


def create_server_app() -> FastAPI:
    application = FastAPI(
        title="Data Tools",
        docs_url=None,
        redoc_url=None,
    )

    app_descriptions: list[dict[str, str]] = []

    for module in APPS:
        for command_name, handler in module.commands.items():
            command_registry.register(command_name, handler)

        if module.router is not None:
            application.include_router(
                module.router,
                prefix=f"/api/{module.app_id}",
                tags=[module.app_id],
            )

        application.mount(
            f"/apps/{module.app_id}",
            StaticFiles(directory=str(module.frontend_dir), html=True),
            name=f"frontend-{module.app_id}",
        )

        app_descriptions.append(
            {
                "id": module.app_id,
                "title": module.title,
                "url": module.frontend_url,
            }
        )

    @application.get("/api/apps")
    def list_apps() -> list[dict[str, str]]:
        return app_descriptions

    shell_dir = resource_path("frontend")

    @application.get("/")
    def main_page() -> FileResponse:
        return FileResponse(shell_dir / "index.html")

    application.mount(
        "/shell",
        StaticFiles(directory=str(shell_dir)),
        name="shell",
    )

    return application
