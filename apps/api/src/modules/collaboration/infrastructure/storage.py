import uuid
from pathlib import Path

from fastapi import UploadFile

from src.platform.config import get_settings
from src.shared_kernel.errors import ValidationError

settings = get_settings()


async def save_upload(file: UploadFile) -> tuple[str, str, int]:
    """Saves an uploaded file to local disk under a random name (never the
    client-supplied filename, to avoid path traversal / collisions) and
    returns (public_url, original_file_name, size_bytes).
    """
    if not file.filename:
        raise ValidationError("Uploaded file must have a filename")

    contents = await file.read()
    if len(contents) > settings.max_upload_size_bytes:
        max_mb = settings.max_upload_size_bytes / (1024 * 1024)
        raise ValidationError(f"File exceeds the {max_mb:.0f}MB upload limit")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(file.filename).suffix
    stored_name = f"{uuid.uuid4()}{extension}"
    (upload_dir / stored_name).write_bytes(contents)

    file_url = f"{settings.api_base_url}/uploads/{stored_name}"
    return file_url, file.filename, len(contents)
