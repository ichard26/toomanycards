from fastapi import APIRouter

router = APIRouter(prefix="/deck", tags=["deck"])

@router.get("/library")
async def get_library():
    return {}


@router.post("/new")
async def create_deck():
    return {}


@router.get("/{deck_id}")
async def get_deck(deck_id: int):
    return {}


@router.put("/{deck_id}")
async def update_deck(deck_id: int):
    return {}


@router.delete("/{deck_id}")
async def delete_deck(deck_id: int):
    return {}
