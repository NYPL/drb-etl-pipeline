import os

def create_authorization_header():
    bearer_token = os.environ.get("AIRTABLE_KEY")

    headers = {"Authorization": f"Bearer {bearer_token}"}

    return headers
