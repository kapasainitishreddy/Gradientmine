"""Single-process container entry point. Public origin must be explicitly configured."""

import os
from .cli import main


def run():
    if not os.getenv("GM_ORIGIN"):
        raise SystemExit("Set GM_ORIGIN to the exact public HTTPS origin before starting this container")
    port = int(os.environ.get("PORT", "8000"))
    if not 1 <= port <= 65535:
        raise SystemExit("PORT must be between 1 and 65535")
    return main(["serve", "--host", "0.0.0.0", "--port", str(port)])


if __name__ == "__main__":
    raise SystemExit(run())
