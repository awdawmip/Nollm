"""M0 compatibility adapters from the mixed GRF workspace to public ports."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path, PurePosixPath
import shutil
from threading import RLock
from uuid import uuid4
from zipfile import ZIP_STORED, BadZipFile, ZipFile, ZipInfo

from nollm_snapshot import ConsistentStatePort


class GRFWorkspaceConsistentStateAdapter:
    """Expose a finite file-first GRF workspace as policy-free snapshot bytes."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace)
        self._lock = RLock()
        self._active_token: object | None = None

    def begin_consistent_read(self) -> object:
        self._lock.acquire()
        if self._active_token is not None:
            self._lock.release()
            raise RuntimeError("consistent read already active")
        token = object()
        self._active_token = token
        return token

    def export_state(self, token: object) -> bytes:
        self._require_token(token)
        return self._export_locked()

    def export_state_bytes(self) -> bytes:
        with self._lock:
            return self._export_locked()

    def _export_locked(self) -> bytes:
        buffer = BytesIO()
        with ZipFile(buffer, "w", compression=ZIP_STORED) as archive:
            if self.workspace.exists():
                for path in sorted(item for item in self.workspace.rglob("*") if item.is_file()):
                    relative = path.relative_to(self.workspace).as_posix()
                    info = ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = ZIP_STORED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, path.read_bytes())
        return buffer.getvalue()

    def import_state(self, payload: bytes) -> None:
        self.import_state_bytes(payload)

    def import_state_bytes(self, payload: bytes) -> None:
        with self._lock:
            if self._active_token is not None:
                raise RuntimeError("cannot import during a consistent read")
            self._restore_atomically(payload)

    def end_consistent_read(self, token: object) -> None:
        self._require_token(token)
        self._active_token = None
        self._lock.release()

    def _require_token(self, token: object) -> None:
        if token is not self._active_token:
            raise ValueError("invalid consistent-read token")

    def _restore_atomically(self, payload: bytes) -> None:
        parent = self.workspace.parent
        parent.mkdir(parents=True, exist_ok=True)
        staging = parent / f".{self.workspace.name}.m0-restore-{uuid4().hex}"
        backup = parent / f".{self.workspace.name}.m0-backup-{uuid4().hex}"
        staging.mkdir()
        moved_original = False
        try:
            try:
                with ZipFile(BytesIO(payload), "r") as archive:
                    for member in archive.infolist():
                        relative = PurePosixPath(member.filename)
                        if relative.is_absolute() or ".." in relative.parts or member.is_dir():
                            if member.is_dir():
                                continue
                            raise ValueError("snapshot contains an unsafe path")
                        target = staging.joinpath(*relative.parts)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(archive.read(member))
            except BadZipFile as error:
                raise ValueError("invalid GRF workspace snapshot") from error
            if self.workspace.exists():
                self.workspace.replace(backup)
                moved_original = True
            staging.replace(self.workspace)
            if moved_original:
                shutil.rmtree(backup)
        except Exception:
            if moved_original and backup.exists() and not self.workspace.exists():
                backup.replace(self.workspace)
            raise
        finally:
            if staging.exists():
                shutil.rmtree(staging)
            if backup.exists() and self.workspace.exists():
                shutil.rmtree(backup)


def workspace_state_port(workspace: Path) -> ConsistentStatePort:
    return GRFWorkspaceConsistentStateAdapter(workspace)
