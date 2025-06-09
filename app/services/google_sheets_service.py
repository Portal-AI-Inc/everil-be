import pandas as pd
import gspread
import requests
from typing import Optional, Dict, Any
from io import StringIO

class GoogleSheetsService:
    def __init__(self):
        self.spreadsheet_id = "1RXXaxbOCtlsOdPDTOhL5R4Wjnrct1jBOaueNSj10Rys"
        self.base_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/export"
        
    def read_sheet_as_csv(self, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        Read a Google Sheet as CSV using the public export URL with multiple fallback methods
        """
        # Try different URL formats for public Google Sheets
        url_formats = [
            # Standard CSV export format
            f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/export?format=csv&gid=0",
            # Alternative public URL format
            f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}",
            # Direct public CSV link
            f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/pub?gid=0&single=true&output=csv",
        ]
        
        for i, csv_url in enumerate(url_formats):
            try:
                print(f"Trying URL format {i+1} for '{sheet_name}': {csv_url}")
                
                response = requests.get(csv_url, timeout=10)
                
                # Don't raise for status immediately, check content first
                if response.status_code == 200:
                    # Check if response has actual CSV content (not HTML error page)
                    content = response.text.strip()
                    if not content:
                        print(f"Empty response for '{sheet_name}' with URL format {i+1}")
                        continue
                        
                    # Check if it's an HTML error page
                    if content.startswith('<!DOCTYPE html>') or content.startswith('<html'):
                        print(f"Received HTML error page for '{sheet_name}' with URL format {i+1}")
                        continue
                    
                    # Try to parse as CSV
                    try:
                        csv_data = StringIO(content)
                        df = pd.read_csv(csv_data)
                        
                        # Clean up empty rows and columns
                        df = df.dropna(how='all').dropna(axis=1, how='all')
                        
                        # Check if DataFrame has meaningful data
                        if df.empty or len(df.columns) == 0:
                            print(f"No meaningful data in '{sheet_name}' with URL format {i+1}")
                            continue
                            
                        print(f"Successfully read Google Sheet '{sheet_name}' with shape {df.shape} using URL format {i+1}")
                        return df
                        
                    except pd.errors.EmptyDataError:
                        print(f"Empty CSV data for '{sheet_name}' with URL format {i+1}")
                        continue
                    except Exception as csv_error:
                        print(f"CSV parsing error for '{sheet_name}' with URL format {i+1}: {csv_error}")
                        continue
                else:
                    print(f"HTTP {response.status_code} for '{sheet_name}' with URL format {i+1}")
                    continue
                    
            except Exception as e:
                print(f"Request error for '{sheet_name}' with URL format {i+1}: {e}")
                continue
        
        print(f"All URL formats failed for Google Sheet '{sheet_name}'")
        return None
    
    def read_sheet_with_gspread(self, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        Alternative method using gspread for public sheets
        """
        try:
            gc = gspread.service_account_from_dict({
                "type": "service_account",
                "project_id": "dummy",
                "private_key_id": "dummy",
                "private_key": "dummy",
                "client_email": "dummy@dummy.iam.gserviceaccount.com",
                "client_id": "dummy",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            })
            
            # Try to open as public sheet
            sheet = gc.open_by_key(self.spreadsheet_id)
            worksheet = sheet.worksheet(sheet_name)
            
            # Get all values and convert to DataFrame
            values = worksheet.get_all_values()
            if not values:
                return None
                
            df = pd.DataFrame(values[1:], columns=values[0])
            return df if not df.empty else None
            
        except Exception as e:
            print(f"Error reading with gspread '{sheet_name}': {e}")
            return None
    
    def get_sheet_data(self, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        Get sheet data, trying multiple methods
        """
        # Try CSV export first (most reliable for public sheets)
        df = self.read_sheet_as_csv(sheet_name)
        
        if df is not None and not df.empty:
            return df
            
        # If CSV fails, try alternative sheet names
        alternative_names = {
            "Items": ["ItemsRecipies", "Sheet1"],
            "Recipes": ["ItemsRecipies", "Sheet2"],
        }
        
        for alt_name in alternative_names.get(sheet_name, []):
            df = self.read_sheet_as_csv(alt_name)
            if df is not None and not df.empty:
                return df
        
        print(f"Could not read sheet '{sheet_name}' from Google Sheets")
        return None
    
    def get_items_data(self) -> Optional[pd.DataFrame]:
        """Get items data from Google Sheets"""
        return self.get_sheet_data("Items")
    
    def get_recipes_data(self) -> Optional[pd.DataFrame]:
        """Get recipes data from Google Sheets"""
        return self.get_sheet_data("Recipes")
    
    def debug_sheet_access(self) -> Dict[str, Any]:
        """Debug method to check what's available in the Google Sheet"""
        debug_info = {
            "spreadsheet_id": self.spreadsheet_id,
            "base_url": self.base_url
        }
        
        # Test different URL formats
        test_urls = [
            f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/export?format=csv&gid=0",
            f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/pub?gid=0&single=true&output=csv",
            f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/gviz/tq?tqx=out:csv",
            f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit#gid=0"
        ]
        
        for i, url in enumerate(test_urls):
            try:
                response = requests.get(url, timeout=5)
                debug_info[f"url_{i+1}_status"] = response.status_code
                debug_info[f"url_{i+1}_length"] = len(response.text)
                debug_info[f"url_{i+1}_preview"] = response.text[:100]
                debug_info[f"url_{i+1}_url"] = url
                
                # Check if it looks like CSV
                if response.status_code == 200:
                    content = response.text.strip()
                    is_csv = not (content.startswith('<!DOCTYPE html>') or content.startswith('<html'))
                    debug_info[f"url_{i+1}_is_csv"] = is_csv
                
            except Exception as e:
                debug_info[f"url_{i+1}_error"] = str(e)
                
        return debug_info 