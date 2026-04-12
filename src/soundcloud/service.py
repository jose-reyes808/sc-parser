from __future__ import annotations

from src.models import AppConfig, ExportResult, ParserSettings
from src.soundcloud.client import SoundCloudClient
from src.soundcloud.exporter import ExcelExporter
from src.soundcloud.parser import SoundCloudTitleParser


class LikesExportService:
    def __init__(self, app_config: AppConfig, parser_settings: ParserSettings) -> None:
        self.app_config = app_config
        self.parser_settings = parser_settings
        self.title_parser = SoundCloudTitleParser(parser_settings)
        self.client = SoundCloudClient(
            client_id=app_config.soundcloud_client_id,
            user_id=app_config.soundcloud_user_id,
            title_parser=self.title_parser,
        )
        self.exporter = ExcelExporter(self.title_parser)

    def run(self) -> ExportResult:
        likes = self.client.get_likes()
        print(f"Pages completed. Total likes collected: {len(likes)}")

        if not likes:
            print("No likes fetched. Empty workbooks will still be written.")

        result = self.exporter.export(
            likes=likes,
            tracks_file=self.app_config.tracks_output_file,
            livesets_file=self.app_config.livesets_output_file,
        )

        print("\nBreakdown:")
        print(f"Tracks: {result.track_count}")
        print(f"Live sets: {result.liveset_count}")

        print("\nArtist Source Breakdown:")
        for source, count in result.artist_source_breakdown.items():
            print(f"{source}: {count}")

        print("Done.")
        return result
