import requests

class GumloopGoogleSheetsMCP:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key

    def read_sheet(self, sheet_id, range_):
        url = f"{self.base_url}/google_sheets/read"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {"sheet_id": sheet_id, "range": range_}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def write_sheet(self, sheet_id, range_, values):
        url = f"{self.base_url}/google_sheets/write"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {"sheet_id": sheet_id, "range": range_, "values": values}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json() 