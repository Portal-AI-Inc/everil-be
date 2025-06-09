import pandas as pd
from typing import List, Optional
from uuid import UUID, uuid4
from ..models.item import Item, ItemCreate
from ..services.google_sheets_service import GoogleSheetsService

class ItemRepository:
    def __init__(self, excel_file: str = "items.xlsx", use_google_sheets: bool = True):
        self.excel_file = excel_file
        self.use_google_sheets = use_google_sheets
        self.google_sheets_service = GoogleSheetsService() if use_google_sheets else None
        self._load_data()
    
    def _load_data(self):
        # Try Google Sheets first if enabled
        if self.use_google_sheets and self.google_sheets_service:
            try:
                self.df = self.google_sheets_service.get_items_data()
                if self.df is not None and not self.df.empty:
                    print("Loaded items data from Google Sheets")
                    # Convert string UUIDs back to UUID objects for processing
                    if 'id' in self.df.columns:
                        self.df['id'] = self.df['id'].astype(str)
                    return
                else:
                    print("Google Sheets returned empty data, falling back to local file")
            except Exception as e:
                print(f"Error loading from Google Sheets: {e}, falling back to local file")
        
        # Fallback to local Excel file
        try:
            self.df = pd.read_excel(self.excel_file)
            print(f"Loaded items data from local file: {self.excel_file}")
            # Convert string UUIDs back to UUID objects for processing
            if not self.df.empty and 'id' in self.df.columns:
                self.df['id'] = self.df['id'].astype(str)
        except FileNotFoundError:
            print("No local file found, creating empty DataFrame")
            self.df = pd.DataFrame(columns=['id', 'name', 'description', 'type', 'rarity', 'price', 'stackable', 'max_stack', 'logo_prompt', 'logo_url'])
    
    def _save_data(self):
        # Convert UUIDs to strings for Excel storage
        df_to_save = self.df.copy()
        if not df_to_save.empty and 'id' in df_to_save.columns:
            df_to_save['id'] = df_to_save['id'].astype(str)
        df_to_save.to_excel(self.excel_file, index=False)
    
    def get_all(self) -> List[Item]:
        items = []
        for _, row in self.df.iterrows():
            row_dict = row.to_dict()
            row_dict['id'] = UUID(str(row_dict['id']))
            # Handle NaN values for optional fields
            if pd.isna(row_dict.get('logo_url')):
                row_dict['logo_url'] = None
            if pd.isna(row_dict.get('logo_prompt')):
                row_dict['logo_prompt'] = None
            items.append(Item(**row_dict))
        return items
    
    def get_by_id(self, item_id: UUID) -> Optional[Item]:
        filtered = self.df[self.df['id'] == str(item_id)]
        if filtered.empty:
            return None
        row_dict = filtered.iloc[0].to_dict()
        row_dict['id'] = UUID(str(row_dict['id']))
        # Handle NaN values for optional fields
        if pd.isna(row_dict.get('logo_url')):
            row_dict['logo_url'] = None
        if pd.isna(row_dict.get('logo_prompt')):
            row_dict['logo_prompt'] = None
        return Item(**row_dict)
    
    def get_by_ids(self, item_ids: List[UUID]) -> List[Item]:
        str_ids = [str(item_id) for item_id in item_ids]
        filtered = self.df[self.df['id'].isin(str_ids)]
        items = []
        for _, row in filtered.iterrows():
            row_dict = row.to_dict()
            row_dict['id'] = UUID(str(row_dict['id']))
            # Handle NaN values for optional fields
            if pd.isna(row_dict.get('logo_url')):
                row_dict['logo_url'] = None
            if pd.isna(row_dict.get('logo_prompt')):
                row_dict['logo_prompt'] = None
            items.append(Item(**row_dict))
        return items
    
    def create(self, item: ItemCreate) -> Item:
        new_id = uuid4()
        new_item_dict = item.dict()
        new_item_dict['id'] = str(new_id)
        
        new_row = pd.DataFrame([new_item_dict])
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        self._save_data()
        
        new_item_dict['id'] = new_id
        return Item(**new_item_dict)
    
    def update(self, item_id: UUID, item: ItemCreate) -> Optional[Item]:
        str_id = str(item_id)
        if str_id not in self.df['id'].values:
            return None
        
        item_dict = item.dict()
        item_dict['id'] = str_id
        
        self.df.loc[self.df['id'] == str_id] = pd.Series(item_dict)
        self._save_data()
        
        item_dict['id'] = item_id
        return Item(**item_dict)
    
    def delete(self, item_id: UUID) -> bool:
        str_id = str(item_id)
        if str_id not in self.df['id'].values:
            return False
        
        self.df = self.df[self.df['id'] != str_id]
        self._save_data()
        return True 