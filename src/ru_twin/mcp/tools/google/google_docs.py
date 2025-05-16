from typing import Dict, Any, List, Optional, Union
from .google_base import GoogleBaseTool, GoogleToolInputSchema
from googleapiclient.discovery import build
import json

class DocsCreateInputSchema(GoogleToolInputSchema):
    """Schema for creating new documents"""
    title: str
    body: Optional[Dict[str, Any]] = None

class DocsEditInputSchema(GoogleToolInputSchema):
    """Schema for editing documents"""
    document_id: str
    requests: List[Dict[str, Any]]

class DocsFormatInputSchema(GoogleToolInputSchema):
    """Schema for formatting text"""
    document_id: str
    range: Dict[str, Any]
    format: Dict[str, Any]

class DocsInsertInputSchema(GoogleToolInputSchema):
    """Schema for inserting elements"""
    document_id: str
    location: Dict[str, Any]
    content: Dict[str, Any]

class DocsExportInputSchema(GoogleToolInputSchema):
    """Schema for exporting documents"""
    document_id: str
    mime_type: str  # e.g., "application/pdf", "text/plain"

class DocsShareInputSchema(GoogleToolInputSchema):
    """Schema for sharing documents"""
    document_id: str
    email: str
    role: str  # "reader", "commenter", "writer", "owner"
    notify: Optional[bool] = True

class DocsCreateTool(GoogleBaseTool):
    """Tool for creating new Google Docs documents"""
    
    def __init__(self):
        super().__init__(
            name="docs_create",
            description="Create new Google Docs documents",
            scopes=["https://www.googleapis.com/auth/documents"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('docs', 'v1', credentials=self.credentials)
        drive_service = build('drive', 'v3', credentials=self.credentials)
        
        try:
            # Create empty document
            file_metadata = {
                'name': input_data["title"],
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            file = drive_service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            document_id = file.get('id')
            
            # If initial body is provided, update the document
            if input_data.get("body"):
                requests = [{
                    'insertText': {
                        'location': {
                            'index': 1
                        },
                        'text': json.dumps(input_data["body"])
                    }
                }]
                
                service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': requests}
                ).execute()
            
            return {
                "document_id": document_id,
                "document_url": f"https://docs.google.com/document/d/{document_id}/edit"
            }
        except Exception as e:
            raise Exception(f"Failed to create document: {str(e)}")

class DocsEditTool(GoogleBaseTool):
    """Tool for editing content in Google Docs"""
    
    def __init__(self):
        super().__init__(
            name="docs_edit",
            description="Edit content in Google Docs",
            scopes=["https://www.googleapis.com/auth/documents"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('docs', 'v1', credentials=self.credentials)
        
        try:
            result = service.documents().batchUpdate(
                documentId=input_data["document_id"],
                body={'requests': input_data["requests"]}
            ).execute()
            
            return {
                "replies": result.get('replies', []),
                "writeControl": result.get('writeControl')
            }
        except Exception as e:
            raise Exception(f"Failed to edit document: {str(e)}")

class DocsFormatTool(GoogleBaseTool):
    """Tool for formatting text and paragraphs"""
    
    def __init__(self):
        super().__init__(
            name="docs_format",
            description="Format text and paragraphs",
            scopes=["https://www.googleapis.com/auth/documents"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('docs', 'v1', credentials=self.credentials)
        
        try:
            requests = [{
                'updateParagraphStyle': {
                    'range': input_data["range"],
                    'paragraphStyle': input_data["format"],
                    'fields': '*'
                }
            }]
            
            result = service.documents().batchUpdate(
                documentId=input_data["document_id"],
                body={'requests': requests}
            ).execute()
            
            return {"replies": result.get('replies', [])}
        except Exception as e:
            raise Exception(f"Failed to format document: {str(e)}")

class DocsInsertTool(GoogleBaseTool):
    """Tool for inserting images, tables, and other elements"""
    
    def __init__(self):
        super().__init__(
            name="docs_insert",
            description="Insert images, tables, and other elements",
            scopes=["https://www.googleapis.com/auth/documents"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('docs', 'v1', credentials=self.credentials)
        
        try:
            requests = [{
                'insertContent': {
                    'location': input_data["location"],
                    'content': input_data["content"]
                }
            }]
            
            result = service.documents().batchUpdate(
                documentId=input_data["document_id"],
                body={'requests': requests}
            ).execute()
            
            return {"replies": result.get('replies', [])}
        except Exception as e:
            raise Exception(f"Failed to insert content: {str(e)}")

class DocsExportTool(GoogleBaseTool):
    """Tool for exporting documents to different formats"""
    
    def __init__(self):
        super().__init__(
            name="docs_export",
            description="Export documents to different formats",
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        drive_service = build('drive', 'v3', credentials=self.credentials)
        
        try:
            request = drive_service.files().export_media(
                fileId=input_data["document_id"],
                mimeType=input_data["mime_type"]
            )
            
            # Get the exported content
            content = request.execute()
            
            return {
                "content": content,
                "mime_type": input_data["mime_type"]
            }
        except Exception as e:
            raise Exception(f"Failed to export document: {str(e)}")

class DocsShareTool(GoogleBaseTool):
    """Tool for managing document sharing and permissions"""
    
    def __init__(self):
        super().__init__(
            name="docs_share",
            description="Manage document sharing and permissions",
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
                fileId=input_data["document_id"],
                body=user_permission,
                sendNotificationEmail=input_data.get("notify", True)
            ).execute()
            
            return {
                "permission_id": result.get('id'),
                "role": result.get('role'),
                "type": result.get('type')
            }
        except Exception as e:
            raise Exception(f"Failed to share document: {str(e)}") 