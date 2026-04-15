from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.config import SettingsLoader
from src.models import PendingImportRequest
from src.soundcloud.client import SoundCloudClient
from src.webapp.queue import create_queue
from src.webapp.spotify_oauth import SpotifyOAuthService
from src.webapp.storage import ImportJobStore
from src.webapp.tasks import run_import_job


def create_app() -> FastAPI:
    project_root = Path(__file__).resolve().parents[2]
    settings_loader = SettingsLoader(project_root)
    web_config = settings_loader.load_web_app_config()
    templates = Jinja2Templates(directory=str(project_root / "templates"))
    store = ImportJobStore(web_config.database_url)
    oauth_service = SpotifyOAuthService(web_config)
    queue = create_queue(web_config.redis_url)

    app = FastAPI(title="SoundCloud Parser Web App")
    app.add_middleware(SessionMiddleware, secret_key=web_config.session_secret)

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request) -> HTMLResponse:
        flash_message = request.session.pop("flash_message", None)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "flash_message": flash_message,
                "app_base_url": web_config.app_base_url,
            },
        )

    @app.post("/imports/start")
    async def start_import(
        request: Request,
        soundcloud_profile_url: str = Form(...),
        playlist_name: str = Form("SoundCloud Likes"),
        start_from_bottom: str | None = Form(None),
    ) -> RedirectResponse:
        try:
            soundcloud_user_id = SoundCloudClient.resolve_user_id(
                client_id=web_config.soundcloud_client_id,
                profile_input=soundcloud_profile_url,
                request_timeout=web_config.request_timeout,
            )
        except Exception as error:
            request.session["flash_message"] = f"SoundCloud profile could not be resolved: {error}"
            return RedirectResponse("/", status_code=303)

        pending_request = PendingImportRequest(
            soundcloud_user_id=soundcloud_user_id,
            playlist_name=playlist_name.strip() or "SoundCloud Likes",
            start_from_bottom=start_from_bottom == "on",
        )
        oauth_state = oauth_service.generate_state()

        request.session["pending_import"] = {
            "soundcloud_profile_url": soundcloud_profile_url.strip(),
            "soundcloud_user_id": pending_request.soundcloud_user_id,
            "playlist_name": pending_request.playlist_name,
            "start_from_bottom": pending_request.start_from_bottom,
        }
        request.session["spotify_oauth_state"] = oauth_state

        return RedirectResponse(
            oauth_service.build_authorize_url(oauth_state),
            status_code=303,
        )

    @app.get("/auth/spotify/callback")
    async def spotify_callback(
        request: Request,
        code: str | None = None,
        state: str | None = None,
        error: str | None = None,
    ) -> RedirectResponse:
        if error:
            request.session["flash_message"] = f"Spotify authorization failed: {error}"
            return RedirectResponse("/", status_code=303)

        expected_state = request.session.get("spotify_oauth_state")
        pending_payload = request.session.get("pending_import")

        if not code or not state or state != expected_state or not pending_payload:
            request.session["flash_message"] = "Spotify authorization could not be completed."
            return RedirectResponse("/", status_code=303)

        tokens = oauth_service.exchange_code(code)
        profile = oauth_service.get_current_user_profile(tokens.access_token)

        pending_request = PendingImportRequest(
            soundcloud_user_id=str(pending_payload["soundcloud_user_id"]),
            playlist_name=str(pending_payload["playlist_name"]),
            start_from_bottom=bool(pending_payload["start_from_bottom"]),
        )

        job = store.create_job(
            request=pending_request,
            soundcloud_client_id=web_config.soundcloud_client_id,
            spotify_tokens=tokens,
            spotify_user_id=str(profile.get("id")) if profile.get("id") else None,
            spotify_display_name=str(profile.get("display_name")) if profile.get("display_name") else None,
        )

        request.session.pop("pending_import", None)
        request.session.pop("spotify_oauth_state", None)
        queue.enqueue(run_import_job, job.id, job_timeout="30m")

        return RedirectResponse(f"/imports/{job.id}", status_code=303)

    @app.get("/imports/{job_id}", response_class=HTMLResponse)
    async def import_status(request: Request, job_id: str) -> HTMLResponse:
        try:
            job = store.get_job(job_id)
        except KeyError:
            return templates.TemplateResponse(
                request=request,
                name="import_not_found.html",
                context={"job_id": job_id},
                status_code=404,
            )

        return templates.TemplateResponse(
            request=request,
            name="import_status.html",
            context={"job": job},
        )

    return app
