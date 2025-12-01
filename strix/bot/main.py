import argparse
import logging
import os

from .config import load_config
from .fs_api import FileSystemControlAPI
from .service import run
from .strix_control_api import StrixControlAPI


def build_control_api(mode: str, root: str) -> object:
    if mode == "fs":
        return FileSystemControlAPI(root_path=root)
    return StrixControlAPI(root_path=root)


def main() -> None:
    parser = argparse.ArgumentParser(description="Strix Telegram bot service")
    parser.add_argument(
        "--mode",
        choices=["strix", "fs"],
        default=os.getenv("BOT_MODE", "strix"),
        help="Control mode: strix (start/stop runs) or fs (read-only browsing).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    cfg = load_config()
    control_api = build_control_api(args.mode, cfg.root_path)
    run(control_api, cfg)


if __name__ == "__main__":
    main()
