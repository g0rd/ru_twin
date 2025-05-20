import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Teller API credentials
TELLER_APP_ID = os.getenv("TELLER_APP_ID")
TELLER_SIGNING_KEY = os.getenv("TELLER_SIGNING_KEY")

# Your webhook URL - replace with your actual URL
# For local development with ngrok:
# WEBHOOK_URL = "https://your-ngrok-url.ngrok.io/webhook/teller"
# For local testing only:
WEBHOOK_URL = "https://028a-2001-5a8-4639-400-e050-1721-a063-3a41.ngrok-free.app/webhook/teller"

def register_webhook():
    """
    Register a webhook with Teller API
    """
    headers = {
        "Authorization": f"Bearer {TELLER_SIGNING_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "url": WEBHOOK_URL,
        "events": [
            "enrollment.disconnected",
            "transactions.processed",
            "account.number_verification.processed"
        ]
    }
    
    try:
        response = requests.post(
            f"https://api.teller.io/applications/{TELLER_APP_ID}/webhooks",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        print("Webhook registered successfully!")
        print("Response:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error registering webhook: {e}")
        if hasattr(e.response, 'text'):
            print("Response:", e.response.text)

if __name__ == "__main__":
    register_webhook() 