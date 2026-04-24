from fastapi import APIRouter, Depends

from api.deps import require_user

router = APIRouter(tags=["me"])


@router.get("/me")
def get_me(user: dict = Depends(require_user)):
    return {"user": user}
