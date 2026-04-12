from __future__ import annotations

import argparse
from pathlib import Path

from src.config import SettingsLoader
from src.spotify.client import SpotifyClient
from src.spotify.matcher import SpotifyTrackMatcher
from src.spotify.service import SpotifyMatchService


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Match SoundCloud export rows to Spotify tracks.",
    )
    parser.add_argument(
        "--input-file",
        default="soundcloud_likes.xlsx",
        help="Input Excel file containing Artist and Song columns.",
    )
    parser.add_argument(
        "--output-file",
        default="spotify_matches.xlsx",
        help="Output Excel file with Spotify match columns appended.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of rows to process. Use 0 to process all rows.",
    )
    parser.add_argument(
        "--create-playlist",
        action="store_true",
        help="Create a Spotify playlist from matched tracks.",
    )
    parser.add_argument(
        "--playlist-name",
        default="SoundCloud Imports",
        help="Playlist name to use when --create-playlist is enabled.",
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="Create a public playlist. Defaults to private.",
    )
    return parser


def main() -> None:
    args = build_argument_parser().parse_args()
    project_root = Path(__file__).resolve().parent
    settings_loader = SettingsLoader(project_root)

    spotify_config = settings_loader.load_spotify_config()
    spotify_client = SpotifyClient(spotify_config)
    spotify_matcher = SpotifyTrackMatcher()
    spotify_service = SpotifyMatchService(spotify_client, spotify_matcher)

    summary = spotify_service.run(
        input_file=project_root / args.input_file,
        output_file=project_root / args.output_file,
        row_limit=args.limit,
        create_playlist=args.create_playlist,
        playlist_name=args.playlist_name,
        playlist_public=args.public,
    )

    print("\nSpotify Match Summary:")
    print(f"Rows processed: {summary.rows_processed}")
    print(f"Matched: {summary.rows_matched}")
    print(f"Unmatched: {summary.rows_unmatched}")
    print(f"Output file: {summary.output_file.name}")

    if summary.playlist_id:
        print(f"Playlist created: {summary.playlist_id}")
        if summary.playlist_url:
            print(f"Playlist URL: {summary.playlist_url}")


if __name__ == "__main__":
    main()
