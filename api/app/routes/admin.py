from typing import Dict

from fastapi import APIRouter

from ..database import db
from ..models import User

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/list-users")
async def list_users() -> Dict[str, User]:
    # TODO: add authentication
    return db.get("users")
