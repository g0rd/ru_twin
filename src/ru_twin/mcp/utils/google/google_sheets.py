from typing import Dict, Any, List, Optional, Union
from .google_base import GoogleBaseTool, GoogleToolInputSchema
from googleapiclient.discovery import build
import json

class SheetsReadInputSchema(GoogleToolInputSchema):
    """Schema for reading data from sheets"""
    spreadsheet_id: str
    range: str
    value_render_option: Optional[str] = "FORMATTED_VALUE"

class SheetsWriteInputSchema(GoogleToolInputSchema):
    """Schema for writing data to sheets"""
    spreadsheet_id: str
    range: str
    values: List[List[Any]]
    value_input_option: Optional[str] = "USER_ENTERED"

class SheetsFormatInputSchema(GoogleToolInputSchema):
    """Schema for formatting cells"""
    spreadsheet_id: str
    range: str
    format: Dict[str, Any]

class SheetsCreateInputSchema(GoogleToolInputSchema):
    """Schema for creating new sheets"""
    title: str
    sheets: Optional[List[Dict[str, Any]]] = None

class SheetsShareInputSchema(GoogleToolInputSchema):
    """Schema for sharing sheets"""
    spreadsheet_id: str
    email: str
    role: str  # "reader", "commenter", "writer", "owner"
    notify: Optional[bool] = True

class SheetsFormulasInputSchema(GoogleToolInputSchema):
    """Schema for working with formulas"""
    spreadsheet_id: str
    range: str
    formula: str

class SheetsReadTool(GoogleBaseTool):
    """Tool for reading data from Google Sheets"""
    
    def __init__(self):
        super().__init__(
            name="sheets_read",
            description="Read data from Google Sheets",
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('sheets', 'v4', credentials=self.credentials)
        
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=input_data["spreadsheet_id"],
                range=input_data["range"],
                valueRenderOption=input_data.get("value_render_option", "FORMATTED_VALUE")
            ).execute()
            
            return {
                "values": result.get('values', []),
                "range": result.get('range'),
                "majorDimension": result.get('majorDimension')
            }
        except Exception as e:
            raise Exception(f"Failed to read sheet data: {str(e)}")

class SheetsWriteTool(GoogleBaseTool):
    """Tool for writing data to Google Sheets"""
    
    def __init__(self):
        super().__init__(
            name="sheets_write",
            description="Write data to Google Sheets",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('sheets', 'v4', credentials=self.credentials)
        
        try:
            body = {
                'values': input_data["values"]
            }
            
            result = service.spreadsheets().values().update(
                spreadsheetId=input_data["spreadsheet_id"],
                range=input_data["range"],
                valueInputOption=input_data.get("value_input_option", "USER_ENTERED"),
                body=body
            ).execute()
            
            return {
                "updated_cells": result.get('updatedCells'),
                "updated_rows": result.get('updatedRows'),
                "updated_columns": result.get('updatedColumns'),
                "updated_range": result.get('updatedRange')
            }
        except Exception as e:
            raise Exception(f"Failed to write sheet data: {str(e)}")

class SheetsFormatTool(GoogleBaseTool):
    """Tool for formatting cells in Google Sheets"""
    
    def __init__(self):
        super().__init__(
            name="sheets_format",
            description="Format cells and ranges in Google Sheets",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('sheets', 'v4', credentials=self.credentials)
        
        try:
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': 0,  # You might want to make this configurable
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': input_data["format"]
                    },
                    'fields': 'userEnteredFormat'
                }
            }]
            
            body = {
                'requests': requests
            }
            
            result = service.spreadsheets().batchUpdate(
                spreadsheetId=input_data["spreadsheet_id"],
                body=body
            ).execute()
            
            return {"replies": result.get('replies', [])}
        except Exception as e:
            raise Exception(f"Failed to format cells: {str(e)}")

class SheetsCreateTool(GoogleBaseTool):
    """Tool for creating new Google Sheets documents"""
    
    def __init__(self):
        super().__init__(
            name="sheets_create",
            description="Create new Google Sheets documents",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('sheets', 'v4', credentials=self.credentials)
        
        try:
            spreadsheet = {
                'properties': {
                    'title': input_data["title"]
                }
            }
            
            if input_data.get("sheets"):
                spreadsheet['sheets'] = input_data["sheets"]
            
            result = service.spreadsheets().create(body=spreadsheet).execute()
            
            return {
                "spreadsheet_id": result.get('spreadsheetId'),
                "spreadsheet_url": result.get('spreadsheetUrl'),
                "sheets": result.get('sheets', [])
            }
        except Exception as e:
            raise Exception(f"Failed to create spreadsheet: {str(e)}")

class SheetsShareTool(GoogleBaseTool):
    """Tool for managing sharing and permissions"""
    
    def __init__(self):
        super().__init__(
            name="sheets_share",
            description="Manage sharing and permissions",
            scopes=["https://www.googleapis.com/auth/drive.file"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        drive_service = build('drive', 'v3', credentials=self.credentials)
        
        try:
            user_permission = {
                'type': 'user',
                'role': input_data["role"],
                'emailAddress': input_data["email"]
            }
            
            result = drive_service.permissions().create(
                fileId=input_data["spreadsheet_id"],
                body=user_permission,
                sendNotificationEmail=input_data.get("notify", True)
            ).execute()
            
            return {
                "permission_id": result.get('id'),
                "role": result.get('role'),
                "type": result.get('type')
            }
        except Exception as e:
            raise Exception(f"Failed to share spreadsheet: {str(e)}")

class SheetsFormulasTool(GoogleBaseTool):
    """Tool for working with formulas and calculations"""
    
    def __init__(self):
        super().__init__(
            name="sheets_formulas",
            description="Work with formulas and calculations",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('sheets', 'v4', credentials=self.credentials)
        
        try:
            body = {
                'values': [[input_data["formula"]]]
            }
            
            result = service.spreadsheets().values().update(
                spreadsheetId=input_data["spreadsheet_id"],
                range=input_data["range"],
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            
            return {
                "updated_cells": result.get('updatedCells'),
                "updated_range": result.get('updatedRange')
            }
        except Exception as e:
            raise Exception(f"Failed to apply formula: {str(e)}") 