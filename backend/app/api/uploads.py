import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/tasks/{project_id}/{task_id}/{filename}")
async def get_task_screenshot(project_id: uuid.UUID, task_id: uuid.UUID, filename: str):
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = Path(settings.uploads_root) / "tasks" / str(project_id) / str(task_id) / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    media = "image/png"
    if filename.lower().endswith((".jpg", ".jpeg")):
        media = "image/jpeg"
    elif filename.lower().endswith(".webp"):
        media = "image/webp"
    return FileResponse(path, media_type=media)
