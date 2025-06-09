from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from .item import Item

class Recipe(BaseModel):
    id: UUID
    name: str
    result_item_id: UUID
    result_quantity: int
    required_items: str  # comma-separated item UUIDs
    required_quantities: str  # comma-separated quantities
    crafting_time: int
    experience_gain: int

class RecipeCreate(BaseModel):
    name: str
    result_item_id: UUID
    result_quantity: int
    required_items: str
    required_quantities: str
    crafting_time: int
    experience_gain: int

class RecipeWithDetails(Recipe):
    result_item: Optional[Item] = None
    required_item_details: Optional[List[Item]] = None 