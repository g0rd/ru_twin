from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/webhook",
    tags=["webhooks"],
    responses={404: {"description": "Not found"}},
)

def verify_teller_signature(request_body: bytes, signature: str) -> bool:
    """
    Verify the Teller webhook signature.
    """
    webhook_secret = os.getenv("TELLER_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    expected_signature = hmac.new(
        webhook_secret.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)

@router.get("/teller")
async def get_teller_webhook() -> Dict[str, Any]:
    """
    Handle GET requests to the Teller webhook endpoint.
    This is useful for webhook verification and testing.
    """
    return {"status": "Teller webhook endpoint is active"}

@router.post("/teller")
async def handle_teller_webhook(request: Request) -> Dict[str, Any]:
    """
    Handle incoming Teller webhooks.
    """
    # Get the signature from headers
    signature = request.headers.get("Teller-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Teller signature")

    # Read the request body
    body = await request.body()

    # Verify the signature
    if not verify_teller_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse the payload
    payload = await request.json()

    # Get the MCP client from the app state
    mcp_client = request.app.state.mcp_client
    if not mcp_client:
        raise HTTPException(status_code=500, detail="MCP client not initialized")

    # Forward the webhook to the MCP client
    await mcp_client.handle_event("webhook", payload)

    return {"status": "success"} 