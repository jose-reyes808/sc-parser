# SoundCloud Parser

This project is evolving from a local script into a backend-first web app that imports SoundCloud likes, matches them on Spotify, and creates a Spotify playlist for the user through Spotify OAuth.

## Current Direction

The repo now supports two modes:

- legacy local scripts for direct command-line use
- a FastAPI web app scaffold prepared for Render deployment

The web app is the path forward.

## Project Structure

```text
soundcloud-parser/
|-- soundcloud_export_likes.py
|-- spotify_match_from_excel.py
|-- webapp.py
|-- worker.py
|-- render.yaml
|-- parser_settings.example.json
|-- .env.example
|-- templates/
|   |-- import_not_found.html
|   |-- import_status.html
|   `-- index.html
`-- src/
    |-- __init__.py
    |-- config.py
    |-- models.py
    |-- soundcloud/
    |   |-- __init__.py
    |   |-- client.py
    |   |-- exporter.py
    |   |-- parser.py
    |   `-- service.py
    |-- spotify/
    |   |-- __init__.py
    |   |-- client.py
    |   |-- matcher.py
    |   `-- service.py
    `-- webapp/
        |-- __init__.py
        |-- app.py
        |-- import_runner.py
        |-- queue.py
        |-- spotify_api.py
        |-- spotify_oauth.py
        |-- storage.py
        `-- tasks.py
```

## Web App Flow

1. User opens the home page
2. User enters:
   - SoundCloud profile URL
   - desired Spotify playlist name
3. Backend resolves the SoundCloud profile URL to a user ID
4. App redirects the user to Spotify OAuth
5. Spotify redirects back to the app callback
6. Backend creates an import job in Postgres
7. A Redis-backed worker fetches SoundCloud likes, matches them on Spotify, and creates the playlist
8. User watches progress on a status page

No Excel file is needed for the web flow.

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

Start from `.env.example`.

```env
SOUNDCLOUD_CLIENT_ID=your_soundcloud_client_id
SOUNDCLOUD_USER_ID=your_soundcloud_user_id
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
WEBAPP_SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/auth/spotify/callback
WEBAPP_SESSION_SECRET=replace_with_a_long_random_secret
APP_BASE_URL=http://127.0.0.1:8000
APP_ENV=development
DATABASE_URL=sqlite:///webapp.sqlite3
REDIS_URL=redis://localhost:6379/0
```

Notes:

- `SPOTIFY_REDIRECT_URI` is still used by the older CLI script flow
- `WEBAPP_SPOTIFY_REDIRECT_URI` is used by the FastAPI web app
- `SOUNDCLOUD_CLIENT_ID` stays server-side and is not entered by users

## Local Development

Install dependencies:

```bash
pip install -r requirements.txt
```

Start Redis locally if you want to use the worker flow.

Run the web app:

```bash
python webapp.py
```

Run the worker:

```bash
python worker.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Render Deployment

This repo now includes [render.yaml](./render.yaml) for a Render Blueprint deployment.

### Architecture on Render

- Web service: `soundcloud-parser`
- Worker service: `soundcloud-parser-worker`
- Redis: `soundcloud-parser-redis`
- Postgres: `soundcloud-parser-db`

### Deployment Steps

1. Push this repo to GitHub.
2. Create a Render account and connect your GitHub repo.
3. In Render, create a new Blueprint deployment from this repo.
4. Render will read `render.yaml` and provision:
   - web service
   - worker service
   - Redis
   - Postgres
5. Set the required secret/config env vars in Render:
   - `SOUNDCLOUD_CLIENT_ID`
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`
   - `APP_BASE_URL`
   - `SPOTIFY_REDIRECT_URI`
   - `WEBAPP_SPOTIFY_REDIRECT_URI`
6. Let Render generate `WEBAPP_SESSION_SECRET`, or replace it with your own long random secret.
7. Once the web service has a public Render URL, set:
   - `APP_BASE_URL=https://your-render-url.onrender.com`
   - `WEBAPP_SPOTIFY_REDIRECT_URI=https://your-render-url.onrender.com/auth/spotify/callback`
8. In Spotify Developer Dashboard, add that exact production callback URL.
9. Attach your custom domain in Render.
10. Update:
   - `APP_BASE_URL=https://yourdomain.com`
   - `WEBAPP_SPOTIFY_REDIRECT_URI=https://yourdomain.com/auth/spotify/callback`
11. In Spotify Developer Dashboard, add the custom-domain callback too:
   - `https://yourdomain.com/auth/spotify/callback`
12. Redeploy if needed and test the full OAuth flow.

## What I Still Need From You

To finish real public deployment, I still need these from you:

- a Render account connected to this GitHub repo
- a working server-side `SOUNDCLOUD_CLIENT_ID`
- your Spotify app credentials
- the public Render URL once it exists
- your custom domain name once you buy/attach it

## Current MVP Backend Features

- FastAPI app with session support
- Spotify OAuth redirect and callback flow
- Postgres-ready database layer via SQLAlchemy
- Redis-backed RQ job queue
- dedicated worker process for imports
- SoundCloud profile URL resolution on the backend
- SoundCloud likes fetch directly from API
- Spotify matching and playlist creation
- import status page with auto-refresh

## Legacy CLI Scripts

These still exist while the web app is being built out:

```bash
python soundcloud_export_likes.py
python spotify_match_from_excel.py --start-from-bottom --create-playlist --playlist-name "SoundCloud Likes"
```

## Next Good Backend Steps

- store matched and unmatched track rows in Postgres
- add retry / dead-letter handling for failed jobs
- add app-level auth if you want saved import history per user
- support more SoundCloud URL variations and validation
