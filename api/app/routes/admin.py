from typing import Dict

from fastapi import APIRouter

from .. import dependencies as deps
from ..database import db
from ..models import Deck, User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/list-users")
async def list_users(_: deps.AdminUser) -> Dict[str, User]:
    return db.get("users")


@router.get("/list-decks")
async def list_decks(_: deps.AdminUser) -> Dict[str, Deck]:
    return db.get("decks")
