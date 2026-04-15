from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterator
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from src.models import PendingImportRequest, SpotifyTokens


@dataclass(frozen=True)
class ImportJob:
    id: str
    status: str
    soundcloud_user_id: str
    soundcloud_client_id: str
    playlist_name: str
    start_from_bottom: bool
    spotify_access_token: str
    spotify_refresh_token: str | None
    spotify_expires_at: int
    spotify_user_id: str | None
    spotify_display_name: str | None
    playlist_id: str | None
    playlist_url: str | None
    matched_count: int
    unmatched_count: int
    error_message: str | None
    created_at: str
    updated_at: str


class Base(DeclarativeBase):
    pass


class ImportJobRecord(Base):
    __tablename__ = "import_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    soundcloud_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    soundcloud_client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    playlist_name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_from_bottom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    spotify_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    spotify_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    spotify_expires_at: Mapped[int] = mapped_column(Integer, nullable=False)
    spotify_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    spotify_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    playlist_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    playlist_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unmatched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ImportJobStore:
    def __init__(self, database_url: str) -> None:
        normalized_database_url = database_url
        if normalized_database_url.startswith("postgres://"):
            normalized_database_url = normalized_database_url.replace(
                "postgres://",
                "postgresql+psycopg://",
                1,
            )
        elif normalized_database_url.startswith("postgresql://"):
            normalized_database_url = normalized_database_url.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )

        connect_args = {"check_same_thread": False} if normalized_database_url.startswith("sqlite") else {}
        self.engine = create_engine(normalized_database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session)
        Base.metadata.create_all(self.engine)

    def create_job(
        self,
        request: PendingImportRequest,
        soundcloud_client_id: str,
        spotify_tokens: SpotifyTokens,
        spotify_user_id: str | None,
        spotify_display_name: str | None,
    ) -> ImportJob:
        timestamp = self._timestamp()
        record = ImportJobRecord(
            id=uuid4().hex,
            status="pending",
            soundcloud_user_id=request.soundcloud_user_id,
            soundcloud_client_id=soundcloud_client_id,
            playlist_name=request.playlist_name,
            start_from_bottom=request.start_from_bottom,
            spotify_access_token=spotify_tokens.access_token,
            spotify_refresh_token=spotify_tokens.refresh_token,
            spotify_expires_at=spotify_tokens.expires_at,
            spotify_user_id=spotify_user_id,
            spotify_display_name=spotify_display_name,
            playlist_id=None,
            playlist_url=None,
            matched_count=0,
            unmatched_count=0,
            error_message=None,
            created_at=timestamp,
            updated_at=timestamp,
        )

        with self._session() as session:
            session.add(record)

        return self.get_job(record.id)

    def get_job(self, job_id: str) -> ImportJob:
        with self._session() as session:
            record = session.get(ImportJobRecord, job_id)

        if record is None:
            raise KeyError(f"Import job not found: {job_id}")

        return self._record_to_job(record)

    def update_status(self, job_id: str, status: str, error_message: str | None = None) -> None:
        with self._session() as session:
            record = self._require_record(session, job_id)
            record.status = status
            record.error_message = error_message
            record.updated_at = self._timestamp()

    def update_spotify_tokens(self, job_id: str, tokens: SpotifyTokens) -> None:
        with self._session() as session:
            record = self._require_record(session, job_id)
            record.spotify_access_token = tokens.access_token
            record.spotify_refresh_token = tokens.refresh_token
            record.spotify_expires_at = tokens.expires_at
            record.updated_at = self._timestamp()

    def mark_completed(
        self,
        job_id: str,
        matched_count: int,
        unmatched_count: int,
        playlist_id: str | None,
        playlist_url: str | None,
    ) -> None:
        with self._session() as session:
            record = self._require_record(session, job_id)
            record.status = "completed"
            record.matched_count = matched_count
            record.unmatched_count = unmatched_count
            record.playlist_id = playlist_id
            record.playlist_url = playlist_url
            record.updated_at = self._timestamp()

    def _require_record(self, session: Session, job_id: str) -> ImportJobRecord:
        record = session.get(ImportJobRecord, job_id)
        if record is None:
            raise KeyError(f"Import job not found: {job_id}")
        return record

    def _session(self) -> Iterator[Session]:
        class _SessionContext:
            def __init__(self, session_factory: sessionmaker[Session]) -> None:
                self._session = session_factory()

            def __enter__(self) -> Session:
                return self._session

            def __exit__(self, exc_type, exc, tb) -> None:
                if exc_type is None:
                    self._session.commit()
                else:
                    self._session.rollback()
                self._session.close()

        return _SessionContext(self.session_factory)

    @staticmethod
    def _record_to_job(record: ImportJobRecord) -> ImportJob:
        return ImportJob(
            id=record.id,
            status=record.status,
            soundcloud_user_id=record.soundcloud_user_id,
            soundcloud_client_id=record.soundcloud_client_id,
            playlist_name=record.playlist_name,
            start_from_bottom=record.start_from_bottom,
            spotify_access_token=record.spotify_access_token,
            spotify_refresh_token=record.spotify_refresh_token,
            spotify_expires_at=record.spotify_expires_at,
            spotify_user_id=record.spotify_user_id,
            spotify_display_name=record.spotify_display_name,
            playlist_id=record.playlist_id,
            playlist_url=record.playlist_url,
            matched_count=record.matched_count,
            unmatched_count=record.unmatched_count,
            error_message=record.error_message,
            created_at=record.created_at.isoformat(),
            updated_at=record.updated_at.isoformat(),
        )

    @staticmethod
    def _timestamp() -> datetime:
        return datetime.now(timezone.utc)
