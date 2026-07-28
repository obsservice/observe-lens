import hashlib
from asyncio import to_thread
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from observelens_knowledge_base.common.exceptions import ValidationDomainError
from observelens_knowledge_base.config import Settings


@dataclass(frozen=True)
class StoredFile:
    file_name: str
    mime_type: str
    file_size: int
    content_hash: str
    storage_uri: str
    path: Path


class DocumentStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def save_upload(self, tenant_id: int, file: UploadFile) -> StoredFile:
        if not file.filename:
            raise ValidationDomainError("Uploaded file must have a filename")
        tenant_dir = self.settings.storage_path / str(tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(file.filename).suffix
        path = tenant_dir / f"{uuid4()}{suffix}"
        max_bytes = self.settings.max_file_size_mb * 1024 * 1024
        digest = hashlib.sha256()
        total = 0
        with path.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    path.unlink(missing_ok=True)
                    raise ValidationDomainError("Document is too large")
                digest.update(chunk)
                out.write(chunk)
        return StoredFile(
            file_name=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            file_size=total,
            content_hash=digest.hexdigest(),
            storage_uri=str(path),
            path=path,
        )

    async def read_text(self, storage_uri: str) -> str:
        path = Path(storage_uri)
        return await to_thread(path.read_text, encoding="utf-8", errors="ignore")
