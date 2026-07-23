from __future__ import annotations

import socket
import threading
import time

import uvicorn
import webview

from core.desktop_api import DesktopApi
from core.server import create_server_app


HOST = "127.0.0.1"


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return int(sock.getsockname()[1])


def wait_for_server(port: int, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            with socket.create_connection((HOST, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)

    raise RuntimeError("Локальний сервер не запустився")


def main() -> None:
    port = find_free_port()
    application = create_server_app()

    config = uvicorn.Config(
        application,
        host=HOST,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    wait_for_server(port)

    desktop_api = DesktopApi()

    webview.create_window(
        title="COSMOS",
        url=f"http://{HOST}:{port}",
        js_api=desktop_api,
        width=1100,
        height=720,
        min_size=(800, 520),
        text_select=True,
    )

    try:
        webview.start(debug=False)
    finally:
        server.should_exit = True
        server_thread.join(timeout=2)


if __name__ == "__main__":
    main()
