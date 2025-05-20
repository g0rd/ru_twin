from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import hmac
import hashlib
import time
import json
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Load Teller credentials from environment variables
TELLER_APP_ID = os.getenv("TELLER_APP_ID")
TELLER_SIGNING_KEY = os.getenv("TELLER_SIGNING_KEY")

def verify_teller_signature(request_body: bytes, signature_header: str) -> bool:
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
            TELLER_SIGNING_KEY.encode('utf-8'),
            signed_message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False

@app.post("/webhook/teller")
async def teller_webhook(request: Request):
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
    if not verify_teller_signature(body, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse the webhook payload
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Handle different webhook event types
    event_type = payload.get("type")
    
    if event_type == "enrollment.disconnected":
        # Handle enrollment disconnection
        enrollment_id = payload["payload"]["enrollment_id"]
        reason = payload["payload"]["reason"]
        print(f"Enrollment {enrollment_id} disconnected. Reason: {reason}")
        
    elif event_type == "transactions.processed":
        # Handle processed transactions
        transactions = payload["payload"]["transactions"]
        print(f"Processed {len(transactions)} transactions")
        
    elif event_type == "account.number_verification.processed":
        # Handle account verification
        account_id = payload["payload"]["account_id"]
        status = payload["payload"]["status"]
        print(f"Account {account_id} verification status: {status}")
        
    elif event_type == "webhook.test":
        # Handle test webhook
        print("Received test webhook")
        
    else:
        print(f"Received unknown event type: {event_type}")

    return JSONResponse(content={"status": "success"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 