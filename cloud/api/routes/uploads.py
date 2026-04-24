import uuid

from fastapi import APIRouter, Body
from fastapi.responses import Response

from shared.storage import write_object

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/init")
def init_upload(body=Body(...)):
    object_path = f"uploads/{uuid.uuid4()}/{body['file_name']}"
    return {
        "object_path": object_path,
        "upload_url": f"/uploads/dev/{object_path}",
    }


@router.put("/dev/{object_path:path}")
def dev_upload(
    object_path: str, payload: bytes = Body(..., media_type="application/octet-stream")
):
    write_object(object_path, payload)
    return Response(status_code=204)
