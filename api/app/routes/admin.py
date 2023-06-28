from typing import Dict

from fastapi import APIRouter

from .. import dependencies as deps
from ..database import db
from ..models import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/list-users")
async def list_users(_: deps.AdminUser) -> Dict[str, User]:
    return db.get("users")
