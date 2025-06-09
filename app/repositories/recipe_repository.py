import pandas as pd
from typing import List, Optional
from uuid import UUID, uuid4
from ..models.recipe import Recipe, RecipeCreate, RecipeWithDetails
from .item_repository import ItemRepository
from ..services.google_sheets_service import GoogleSheetsService

class RecipeRepository:
    def __init__(self, excel_file: str = "recipes.xlsx", item_repo: ItemRepository = None, use_google_sheets: bool = True):
        self.excel_file = excel_file
        self.use_google_sheets = use_google_sheets
        self.google_sheets_service = GoogleSheetsService() if use_google_sheets else None
        self.item_repo = item_repo or ItemRepository(use_google_sheets=use_google_sheets)
        self._load_data()
    
    def _load_data(self):
        # Try Google Sheets first if enabled
        if self.use_google_sheets and self.google_sheets_service:
            try:
                self.df = self.google_sheets_service.get_recipes_data()
                if self.df is not None and not self.df.empty:
                    print("Loaded recipes data from Google Sheets")
                    # Convert string UUIDs back to UUID objects for processing
                    if 'id' in self.df.columns:
                        self.df['id'] = self.df['id'].astype(str)
                    if 'result_item_id' in self.df.columns:
                        self.df['result_item_id'] = self.df['result_item_id'].astype(str)
                    return
                else:
                    print("Google Sheets returned empty recipes data, falling back to local file")
            except Exception as e:
                print(f"Error loading recipes from Google Sheets: {e}, falling back to local file")
        
        # Fallback to local Excel file
        try:
            self.df = pd.read_excel(self.excel_file)
            print(f"Loaded recipes data from local file: {self.excel_file}")
            # Convert string UUIDs back to UUID objects for processing
            if not self.df.empty:
                if 'id' in self.df.columns:
                    self.df['id'] = self.df['id'].astype(str)
                if 'result_item_id' in self.df.columns:
                    self.df['result_item_id'] = self.df['result_item_id'].astype(str)
        except FileNotFoundError:
            print("No local recipes file found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=['id', 'name', 'result_item_id', 'result_quantity', 
                                          'required_items', 'required_quantities', 
                                          'crafting_time', 'experience_gain'])
    
    def _save_data(self):
        # Convert UUIDs to strings for Excel storage
        df_to_save = self.df.copy()
        if not df_to_save.empty:
            if 'id' in df_to_save.columns:
                df_to_save['id'] = df_to_save['id'].astype(str)
            if 'result_item_id' in df_to_save.columns:
                df_to_save['result_item_id'] = df_to_save['result_item_id'].astype(str)
        df_to_save.to_excel(self.excel_file, index=False)
    
    def get_all(self) -> List[Recipe]:
        recipes = []
        for _, row in self.df.iterrows():
            row_dict = row.to_dict()
            row_dict['id'] = UUID(str(row_dict['id']))
            row_dict['result_item_id'] = UUID(str(row_dict['result_item_id']))
            recipes.append(Recipe(**row_dict))
        return recipes
    
    def get_by_id(self, recipe_id: UUID) -> Optional[Recipe]:
        filtered = self.df[self.df['id'] == str(recipe_id)]
        if filtered.empty:
            return None
        row_dict = filtered.iloc[0].to_dict()
        row_dict['id'] = UUID(str(row_dict['id']))
        row_dict['result_item_id'] = UUID(str(row_dict['result_item_id']))
        return Recipe(**row_dict)
    
    def get_by_id_with_details(self, recipe_id: UUID) -> Optional[RecipeWithDetails]:
        recipe = self.get_by_id(recipe_id)
        if not recipe:
            return None
        
        # Get result item details
        result_item = self.item_repo.get_by_id(recipe.result_item_id)
        
        # Get required items details
        required_item_ids = [UUID(x.strip()) for x in recipe.required_items.split(',')]
        required_items = self.item_repo.get_by_ids(required_item_ids)
        
        return RecipeWithDetails(
            id=recipe.id,
            name=recipe.name,
            result_item_id=recipe.result_item_id,
            result_quantity=recipe.result_quantity,
            required_items=recipe.required_items,
            required_quantities=recipe.required_quantities,
            crafting_time=recipe.crafting_time,
            experience_gain=recipe.experience_gain,
            result_item=result_item,
            required_item_details=required_items
        )
    
    def get_all_with_details(self) -> List[RecipeWithDetails]:
        recipes = self.get_all()
        detailed_recipes = []
        for recipe in recipes:
            detailed = self.get_by_id_with_details(recipe.id)
            if detailed:
                detailed_recipes.append(detailed)
        return detailed_recipes
    
    def create(self, recipe: RecipeCreate) -> Recipe:
        new_id = uuid4()
        new_recipe_dict = recipe.dict()
        new_recipe_dict['id'] = str(new_id)
        new_recipe_dict['result_item_id'] = str(recipe.result_item_id)
        
        new_row = pd.DataFrame([new_recipe_dict])
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        self._save_data()
        
        new_recipe_dict['id'] = new_id
        new_recipe_dict['result_item_id'] = recipe.result_item_id
        return Recipe(**new_recipe_dict)
    
    def update(self, recipe_id: UUID, recipe: RecipeCreate) -> Optional[Recipe]:
        str_id = str(recipe_id)
        if str_id not in self.df['id'].values:
            return None
        
        recipe_dict = recipe.dict()
        recipe_dict['id'] = str_id
        recipe_dict['result_item_id'] = str(recipe.result_item_id)
        
        self.df.loc[self.df['id'] == str_id] = pd.Series(recipe_dict)
        self._save_data()
        
        recipe_dict['id'] = recipe_id
        recipe_dict['result_item_id'] = recipe.result_item_id
        return Recipe(**recipe_dict)
    
    def delete(self, recipe_id: UUID) -> bool:
        str_id = str(recipe_id)
        if str_id not in self.df['id'].values:
            return False
        
        self.df = self.df[self.df['id'] != str_id]
        self._save_data()
        return True 