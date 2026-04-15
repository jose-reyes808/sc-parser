from __future__ import annotations

from pathlib import Path

from redis import Redis
from rq import Worker

from src.config import SettingsLoader


def main() -> None:
    project_root = Path(__file__).resolve().parent
    settings_loader = SettingsLoader(project_root)
    web_config = settings_loader.load_web_app_config()
    redis_connection = Redis.from_url(web_config.redis_url)

    worker = Worker(["imports"], connection=redis_connection)
    worker.work()


if __name__ == "__main__":
    main()
