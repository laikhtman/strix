import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict


@dataclass
class TelegramBotConfig:
    bot_token: str
    webhook_url: str
    allowlisted_user_ids: List[int]
    db_path: str = "bot_state.sqlite"
    root_path: str = "."
    http_host: str | None = None
    http_port: int | None = None
    http_token: str | None = None
    alert_webhook: str | None = None
    rate_limit_seconds: float = 1.0
    global_rate_limit_seconds: float = 0.5
    default_verbosity: str = "high-only"


def _load_env_file(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        env[key.strip()] = val.strip()
    return env


def load_config() -> TelegramBotConfig:
    file_env = _load_env_file(Path(".env"))

    def getenv(name: str, default: str = "") -> str:
        if name in os.environ:
            return os.getenv(name, default) or default
        return file_env.get(name, default)

    token = getenv("BOT_TOKEN", "").strip()
    token_file = getenv("BOT_TOKEN_FILE", "").strip()
    if not token and token_file:
        try:
            token = Path(token_file).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ValueError(f"Failed to read BOT_TOKEN_FILE: {exc}") from exc
    webhook = getenv("WEBHOOK_URL", "").strip()
    allowlist_raw = getenv("ALLOWLIST_IDS", "")
    allowlist: list[int] = []
    for item in allowlist_raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            allowlist.append(int(item))
        except ValueError:
            continue

    http_host = getenv("BOT_HTTP_HOST")
    http_port_raw = getenv("BOT_HTTP_PORT")
    http_port: int | None = None
    if http_port_raw:
        try:
            http_port = int(http_port_raw)
        except ValueError:
            http_port = None

    http_token = getenv("BOT_HTTP_TOKEN")
    alert_webhook = getenv("BOT_ALERT_WEBHOOK")
    rate_limit_seconds = float(getenv("BOT_RATE_LIMIT", "1.0"))
    global_rate_limit_seconds = float(getenv("BOT_GLOBAL_RATE_LIMIT", "0.5"))
    default_verbosity = getenv("BOT_DEFAULT_VERBOSITY", "high-only")

    cfg = TelegramBotConfig(
        bot_token=token,
        webhook_url=webhook,
        allowlisted_user_ids=allowlist,
        db_path=getenv("BOT_DB_PATH", "bot_state.sqlite"),
        root_path=getenv("STRIX_ROOT", "."),
        http_host=http_host,
        http_port=http_port,
        http_token=http_token,
        alert_webhook=alert_webhook,
        rate_limit_seconds=rate_limit_seconds,
        global_rate_limit_seconds=global_rate_limit_seconds,
        default_verbosity=default_verbosity,
    )

    if not cfg.bot_token:
        raise ValueError("BOT_TOKEN is required")
    if not cfg.webhook_url:
        raise ValueError("WEBHOOK_URL is required")
    if not cfg.allowlisted_user_ids:
        raise ValueError("ALLOWLIST_IDS is required (comma-separated Telegram user IDs)")

    return cfg
