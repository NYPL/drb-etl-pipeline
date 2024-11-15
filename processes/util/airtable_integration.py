import os
import requests

def create_authorization_header():
    bearer_token = os.environ.get("AIRTABLE_KEY")

    headers = {"Authorization": f"Bearer {bearer_token}"}

    return headers

def create_airtable_request():

    headers = create_authorization_header()

    response = requests.get('https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=UofMichigan%20Press&maxRecords=3', headers=headers)

    return response.json()
