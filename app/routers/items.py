from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID
from ..models.item import Item, ItemCreate
from ..repositories.item_repository import ItemRepository

router = APIRouter(prefix="/items", tags=["items"])

# Initialize repository with Google Sheets enabled
item_repo = ItemRepository(use_google_sheets=True)

@router.get("/", response_model=List[Item])
async def get_all_items():
    return item_repo.get_all()

@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: UUID):
    item = item_repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post("/", response_model=Item)
async def create_item(item: ItemCreate):
    return item_repo.create(item)

@router.put("/{item_id}", response_model=Item)
async def update_item(item_id: UUID, item: ItemCreate):
    updated_item = item_repo.update(item_id, item)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item

@router.delete("/{item_id}")
async def delete_item(item_id: UUID):
    success = item_repo.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"} 