"""Сервис управления релизами агентов."""

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

from umbrella_server.core.config import Settings
from umbrella_server.core.logging import get_logger
from umbrella_server.domains.releases.exceptions import AgentReleaseNotFoundError
from umbrella_server.domains.releases.schemas import AgentReleaseRead

logger = get_logger(__name__)

CHUNK = 1024 * 256  # 256 KB

# GoReleaser convention: {name}_{version}_{platform}_{arch}[.exe]
_FILENAME_RE = re.compile(
    r'^.+?_(?P<version>\d+\.\d+\.\d+[^_]*)_(?P<platform>linux|windows|macos|darwin)_(?P<arch>amd64|arm64)(?:\.exe)?$'
)
_PLATFORM_ALIAS = {"darwin": "macos"}


def _parse_filename(name: str) -> dict | None:
    m = _FILENAME_RE.match(name)
    if not m:
        return None
    platform = m.group("platform")
    return {
        "version": m.group("version"),
        "platform": _PLATFORM_ALIAS.get(platform, platform),
        "arch": m.group("arch"),
    }


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _to_schema(path: Path) -> AgentReleaseRead | None:
    meta = _parse_filename(path.name)
    if meta is None:
        return None
    stat = path.stat()
    return AgentReleaseRead(
        id=path.name,
        filename=path.name,
        file_size=stat.st_size,
        checksum=_sha256(path),
        uploaded_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        **meta,
    )


class ReleasesService:
    def __init__(self, settings: Settings) -> None:
        self._dir = Path(settings.releases_dir)

    def get(self, release_id: str) -> AgentReleaseRead:
        path = self._dir / release_id
        if not path.is_file():
            raise AgentReleaseNotFoundError(release_id)
        release = _to_schema(path)
        if release is None:
            raise AgentReleaseNotFoundError(release_id)
        return release

    def list(self, *, platform: str | None = None) -> list[AgentReleaseRead]:
        if not self._dir.exists():
            return []
        releases = []
        for path in sorted(self._dir.iterdir()):
            if not path.is_file():
                continue
            r = _to_schema(path)
            if r is None:
                continue
            if platform and r.platform != platform:
                continue
            releases.append(r)
        return releases

    def delete(self, release_id: str) -> None:
        path = self._dir / release_id
        if not path.is_file():
            raise AgentReleaseNotFoundError(release_id)
        path.unlink()
        logger.info("release_deleted", release_id=release_id)

    def file_path(self, release: AgentReleaseRead) -> Path:
        return self._dir / release.filename
