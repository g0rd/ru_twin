from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import hmac
import hashlib
import time
import json
import os
from typing import Dict, Any, Callable
from functools import wraps

class TellerWebhookHandler:
    def __init__(self, app_id: str, signing_key: str):
        self.app_id = app_id
        self.signing_key = signing_key
        self.event_handlers: Dict[str, Callable] = {}

    def verify_signature(self, request_body: bytes, signature_header: str) -> bool:
        """
        Verify the Teller webhook signature to ensure the request is legitimate.
        """
        try:
            # Parse the signature header
            # Format: t=timestamp,v1=signature
            parts = signature_header.split(',')
            timestamp = parts[0].split('=')[1]
            signature = parts[1].split('=')[1]

            # Check if the timestamp is within 3 minutes
            current_time = int(time.time())
            if current_time - int(timestamp) > 180:  # 3 minutes
                return False

            # Create the signed message
            signed_message = f"{timestamp}.{request_body.decode('utf-8')}"

            # Calculate the expected signature
            expected_signature = hmac.new(
                self.signing_key.encode('utf-8'),
                signed_message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False

    def register_handler(self, event_type: str):
        """
        Decorator to register a handler for a specific event type
        """
        def decorator(func: Callable):
            self.event_handlers[event_type] = func
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    async def handle_webhook(self, request: Request) -> JSONResponse:
        """
        Handle incoming Teller webhook events.
        """
        # Get the signature from headers
        signature_header = request.headers.get("Teller-Signature")
        if not signature_header:
            raise HTTPException(status_code=400, detail="Missing Teller-Signature header")

        # Read the request body
        body = await request.body()

        # Verify the signature
        if not self.verify_signature(body, signature_header):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse the webhook payload
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Get the event type and handle it
        event_type = payload.get("type")
        if event_type in self.event_handlers:
            try:
                result = await self.event_handlers[event_type](payload)
                return JSONResponse(content={"status": "success", "result": result})
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        else:
            print(f"Received unhandled event type: {event_type}")
            return JSONResponse(content={"status": "success", "message": "Event type not handled"}) 