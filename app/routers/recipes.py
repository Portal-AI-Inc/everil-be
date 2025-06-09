from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID
from ..models.recipe import Recipe, RecipeCreate, RecipeWithDetails
from ..repositories.recipe_repository import RecipeRepository
from ..repositories.item_repository import ItemRepository

router = APIRouter(prefix="/recipes", tags=["recipes"])

# Initialize repositories with Google Sheets enabled
item_repo = ItemRepository(use_google_sheets=True)
recipe_repo = RecipeRepository(item_repo=item_repo, use_google_sheets=True)

@router.get("/", response_model=List[Recipe])
async def get_all_recipes():
    return recipe_repo.get_all()

@router.get("/detailed", response_model=List[RecipeWithDetails])
async def get_all_recipes_detailed():
    return recipe_repo.get_all_with_details()

@router.get("/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: UUID):
    recipe = recipe_repo.get_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@router.get("/{recipe_id}/detailed", response_model=RecipeWithDetails)
async def get_recipe_detailed(recipe_id: UUID):
    recipe = recipe_repo.get_by_id_with_details(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@router.post("/", response_model=Recipe)
async def create_recipe(recipe: RecipeCreate):
    # Verify result item exists
    if not item_repo.get_by_id(recipe.result_item_id):
        raise HTTPException(status_code=400, detail="Result item not found")
    
    # Verify required items exist
    required_item_ids = [UUID(x.strip()) for x in recipe.required_items.split(',')]
    for item_id in required_item_ids:
        if not item_repo.get_by_id(item_id):
            raise HTTPException(status_code=400, detail=f"Required item {item_id} not found")
    
    return recipe_repo.create(recipe)

@router.put("/{recipe_id}", response_model=Recipe)
async def update_recipe(recipe_id: UUID, recipe: RecipeCreate):
    # Verify result item exists
    if not item_repo.get_by_id(recipe.result_item_id):
        raise HTTPException(status_code=400, detail="Result item not found")
    
    # Verify required items exist
    required_item_ids = [UUID(x.strip()) for x in recipe.required_items.split(',')]
    for item_id in required_item_ids:
        if not item_repo.get_by_id(item_id):
            raise HTTPException(status_code=400, detail=f"Required item {item_id} not found")
    
    updated_recipe = recipe_repo.update(recipe_id, recipe)
    if not updated_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return updated_recipe

@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: UUID):
    success = recipe_repo.delete(recipe_id)
    if not success:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"message": "Recipe deleted successfully"} 