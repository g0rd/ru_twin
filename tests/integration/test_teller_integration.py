# Integration tests for Teller API interaction

import pytest
import os
from ru_twin.mcp_clients.teller import TellerClient
from dotenv import load_dotenv

load_dotenv()

# This would typically require a live or mocked Teller instance/token
@pytest.fixture
def teller_client():
    access_token = os.getenv("TELLER_ACCESS_TOKEN")
    if not access_token:
        pytest.skip("TELLER_ACCESS_TOKEN environment variable not set")
    return TellerClient(access_token=access_token)


@pytest.mark.skip(reason="Teller integration test not yet implemented")
def test_teller_get_accounts(teller_client):
    try:
        accounts = teller_client.get_accounts()
        assert isinstance(accounts, list)
        # Add more assertions to check account data
    except Exception as e:
        pytest.fail(f"API call failed: {e}")


@pytest.mark.skip(reason="Teller integration test not yet implemented")
def test_teller_get_transactions(teller_client):
    try:
        accounts = teller_client.get_accounts()
        if accounts:
            account_id = accounts[0].id
            transactions = teller_client.get_account_transactions(account_id=account_id)
            assert isinstance(transactions, list)
            # Add more assertions to check transaction data
        else:
            pytest.skip("No accounts found for testing")
    except Exception as e:
        pytest.fail(f"API call failed: {e}")


@pytest.mark.skip(reason="Teller integration test not yet implemented")
def test_teller_get_balance(teller_client):
    try:
        accounts = teller_client.get_accounts()
        if accounts:
            account_id = accounts[0].id
            balance = teller_client.get_account_balance(account_id=account_id)
            assert balance is not None
            assert isinstance(balance.ledger, float)
            # Add more assertions to check balance data
        else:
            pytest.skip("No accounts found for testing")
    except Exception as e:
        pytest.fail(f"API call failed: {e}")
