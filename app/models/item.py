from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class Item(BaseModel):
    id: UUID
    name: str
    description: str
    type: str
    rarity: str
    price: int
    stackable: bool
    max_stack: int
    logo_prompt: Optional[str] = None
    logo_url: Optional[str] = None

class ItemCreate(BaseModel):
    name: str
    description: str
    type: str
    rarity: str
    price: int
    stackable: bool
    max_stack: int
    logo_prompt: Optional[str] = None
    logo_url: Optional[str] = None 