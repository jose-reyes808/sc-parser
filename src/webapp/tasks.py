from __future__ import annotations

from pathlib import Path

from src.config import SettingsLoader
from src.webapp.import_runner import WebImportRunner
from src.webapp.spotify_oauth import SpotifyOAuthService
from src.webapp.storage import ImportJobStore


def run_import_job(job_id: str) -> None:
    project_root = Path(__file__).resolve().parents[2]
    settings_loader = SettingsLoader(project_root)
    web_config = settings_loader.load_web_app_config()
    store = ImportJobStore(web_config.database_url)
    oauth_service = SpotifyOAuthService(web_config)
    runner = WebImportRunner(settings_loader, store, oauth_service)
    runner.run_import(job_id)
