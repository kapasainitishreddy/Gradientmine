"""Explicit runtime settings. Mainnet is intentionally unsupported."""

from dataclasses import dataclass, field
from pathlib import Path
import os
from urllib.parse import urlparse


@dataclass(frozen=True)
class Settings:
    root: Path = field(default_factory=lambda: Path(".local/gradientmine"))
    mode: str = "local"
    origin: str = "http://127.0.0.1:8000"
    rpc_url: str = "https://api.devnet.solana.com"
    program_id: str = ""
    task_seed: int = 42
    validator_key: str = ""
    max_jobs: int = 1000

    def __post_init__(self):
        if self.mode not in {"local", "devnet"}:
            raise ValueError("GM_MODE must be local or devnet; mainnet is not supported")
        parsed = urlparse(self.origin)
        if (
            parsed.username
            or parsed.password
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
            or not parsed.hostname
            or not (
                parsed.scheme == "https"
                or (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost") and parsed.port)
            )
        ):
            raise ValueError(
                "GM_ORIGIN must be an HTTPS origin or explicit loopback origin, with no path or credentials"
            )
        object.__setattr__(self, "origin", self.origin.rstrip("/"))

    @classmethod
    def from_env(cls):
        return cls(
            root=Path(os.getenv("GM_DATA_DIR", ".local/gradientmine")),
            mode=os.getenv("GM_MODE", "local"),
            origin=os.getenv("GM_ORIGIN", "http://127.0.0.1:8000"),
            rpc_url=os.getenv("GM_RPC_URL", "https://api.devnet.solana.com"),
            program_id=os.getenv("GM_PROGRAM_ID", ""),
            validator_key=os.getenv("GM_VALIDATOR_KEY", ""),
            task_seed=int(os.getenv("GM_TASK_SEED", "42")),
        )
