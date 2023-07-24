from fastapi import APIRouter

from .. import dependencies as deps
from ..models import AuthSession, Deck, User
from ..utils import flatten

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/list-users")
async def list_users(_: deps.SignedInAdmin, db: deps.DBConnection) -> list[User]:
    users = []
    for row in db.execute("SELECT * FROM users;"):
        cur = db.execute("SELECT id FROM decks WHERE owner = ?;", [row["username"]])
        users.append(dict(**row, decks=flatten(cur.fetchall())))
    return users


@router.get("/list-decks")
async def list_decks(_: deps.SignedInAdmin, db: deps.DBConnection) -> list[Deck]:
    decks = []
    for row in db.execute("SELECT * FROM decks;"):
        cur = db.execute("SELECT * FROM cards WHERE deck_id = ?;", [row["id"]])
        decks.append(Deck(**row, cards=list(cur)))
    return decks


@router.get("/list-sessions")
async def list_sessions(_: deps.SignedInAdmin, db: deps.DBConnection) -> list[AuthSession]:
    return db.get_sign_in_sessions(username=None)
