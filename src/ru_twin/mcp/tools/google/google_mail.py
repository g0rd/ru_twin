from typing import Dict, Any, List, Optional
from .google_base import GoogleBaseTool, GoogleToolInputSchema
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
import json

class GmailSendInputSchema(GoogleToolInputSchema):
    """Schema for sending emails"""
    to: str
    subject: str
    body: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None

class GmailReadInputSchema(GoogleToolInputSchema):
    """Schema for reading emails"""
    query: str
    max_results: Optional[int] = 10

class GmailDraftInputSchema(GoogleToolInputSchema):
    """Schema for creating drafts"""
    to: str
    subject: str
    body: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None

class GmailLabelsInputSchema(GoogleToolInputSchema):
    """Schema for managing labels"""
    action: str  # "list", "create", "delete"
    label_name: Optional[str] = None
    label_color: Optional[Dict[str, str]] = None

class GmailSearchInputSchema(GoogleToolInputSchema):
    """Schema for searching emails"""
    query: str
    max_results: Optional[int] = 10

class GmailSendTool(GoogleBaseTool):
    """Tool for sending emails using Gmail API"""
    
    def __init__(self):
        super().__init__(
            name="gmail_send",
            description="Send emails using Gmail API",
            scopes=["https://www.googleapis.com/auth/gmail.send"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('gmail', 'v1', credentials=self.credentials)
        
        message = MIMEText(input_data["body"])
        message['to'] = input_data["to"]
        message['subject'] = input_data["subject"]
        
        if input_data.get("cc"):
            message['cc'] = ", ".join(input_data["cc"])
        if input_data.get("bcc"):
            message['bcc'] = ", ".join(input_data["bcc"])
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        
        try:
            message = service.users().messages().send(
                userId='me', body=body).execute()
            return {"message_id": message['id'], "status": "sent"}
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")

class GmailReadTool(GoogleBaseTool):
    """Tool for reading emails from Gmail inbox"""
    
    def __init__(self):
        super().__init__(
            name="gmail_read",
            description="Read emails from Gmail inbox",
            scopes=["https://www.googleapis.com/auth/gmail.readonly"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('gmail', 'v1', credentials=self.credentials)
        
        try:
            results = service.users().messages().list(
                userId='me',
                q=input_data["query"],
                maxResults=input_data.get("max_results", 10)
            ).execute()
            
            messages = results.get('messages', [])
            email_list = []
            
            for message in messages:
                msg = service.users().messages().get(
                    userId='me', id=message['id']).execute()
                headers = msg['payload']['headers']
                subject = next(h['value'] for h in headers if h['name'] == 'Subject')
                sender = next(h['value'] for h in headers if h['name'] == 'From')
                
                email_list.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'snippet': msg['snippet']
                })
            
            return {"emails": email_list}
        except Exception as e:
            raise Exception(f"Failed to read emails: {str(e)}")

class GmailDraftTool(GoogleBaseTool):
    """Tool for creating and managing email drafts"""
    
    def __init__(self):
        super().__init__(
            name="gmail_draft",
            description="Create and manage email drafts",
            scopes=["https://www.googleapis.com/auth/gmail.modify"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('gmail', 'v1', credentials=self.credentials)
        
        message = MIMEText(input_data["body"])
        message['to'] = input_data["to"]
        message['subject'] = input_data["subject"]
        
        if input_data.get("cc"):
            message['cc'] = ", ".join(input_data["cc"])
        if input_data.get("bcc"):
            message['bcc'] = ", ".join(input_data["bcc"])
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'message': {'raw': raw}}
        
        try:
            draft = service.users().drafts().create(
                userId='me', body=body).execute()
            return {"draft_id": draft['id'], "status": "created"}
        except Exception as e:
            raise Exception(f"Failed to create draft: {str(e)}")

class GmailLabelsTool(GoogleBaseTool):
    """Tool for managing Gmail labels"""
    
    def __init__(self):
        super().__init__(
            name="gmail_labels",
            description="Manage Gmail labels and categories",
            scopes=["https://www.googleapis.com/auth/gmail.modify"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('gmail', 'v1', credentials=self.credentials)
        
        try:
            if input_data["action"] == "list":
                results = service.users().labels().list(userId='me').execute()
                return {"labels": results.get('labels', [])}
            
            elif input_data["action"] == "create":
                label_object = {
                    'name': input_data["label_name"],
                    'labelListVisibility': 'labelShow',
                    'messageListVisibility': 'show'
                }
                if input_data.get("label_color"):
                    label_object['color'] = input_data["label_color"]
                
                label = service.users().labels().create(
                    userId='me', body=label_object).execute()
                return {"label": label}
            
            elif input_data["action"] == "delete":
                service.users().labels().delete(
                    userId='me', id=input_data["label_name"]).execute()
                return {"status": "deleted"}
            
            else:
                raise ValueError("Invalid action specified")
                
        except Exception as e:
            raise Exception(f"Failed to manage labels: {str(e)}")

class GmailSearchTool(GoogleBaseTool):
    """Tool for searching through Gmail messages"""
    
    def __init__(self):
        super().__init__(
            name="gmail_search",
            description="Search through Gmail messages",
            scopes=["https://www.googleapis.com/auth/gmail.readonly"]
        )

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        service = build('gmail', 'v1', credentials=self.credentials)
        
        try:
            results = service.users().messages().list(
                userId='me',
                q=input_data["query"],
                maxResults=input_data.get("max_results", 10)
            ).execute()
            
            messages = results.get('messages', [])
            search_results = []
            
            for message in messages:
                msg = service.users().messages().get(
                    userId='me', id=message['id']).execute()
                
                headers = msg['payload']['headers']
                subject = next(h['value'] for h in headers if h['name'] == 'Subject')
                sender = next(h['value'] for h in headers if h['name'] == 'From')
                
                search_results.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'snippet': msg['snippet'],
                    'labels': msg['labelIds']
                })
            
            return {"results": search_results}
        except Exception as e:
            raise Exception(f"Failed to search messages: {str(e)}") 