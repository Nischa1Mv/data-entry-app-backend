from .login import login_to_erp
import os
import json
import requests
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()

API_BASE = os.getenv("API_BASE")

def get_doctype_count(session: requests.Session, linked_doctype: str) -> int:
    """Fetches the total count of documents matching the filters."""
    # 1. Define the dedicated Frappe endpoint for counting
    COUNT_ENDPOINT = f"{API_BASE}/api/method/frappe.client.get_count"
    
    count_params = {
        "doctype": linked_doctype,
    }
    
    # 2. Make the count request
    count_response = session.get(
        COUNT_ENDPOINT,
        params=count_params,
        timeout=10,
    )
    if count_response.status_code == 200:
        try:
            # The count is returned as an integer in the 'message' field
            return int(count_response.json().get("message", 0))
        except (ValueError, json.JSONDecodeError):
            print("Warning: Could not parse count response. Defaulting to 1000 limit.")
            return 1000
    else:
        # Fallback if the count API fails (e.g., connection or permission error)
        print(f"Warning: Failed to get count ({count_response.status_code}). Defaulting to 1000 limit.")
        return 1000

def fetch_link_options(linked_doctype: str):
    session = login_to_erp()

    # Use the dynamic count to decide how many records to request
    total_count = get_doctype_count(session, linked_doctype)
    if total_count <= 0:
        raise HTTPException(status_code=404, detail=f"No data found for DocType: {linked_doctype}")

    response = session.get(
        f"{API_BASE}/api/resource/{linked_doctype}",
        headers={"Content-Type": "application/json"},
        timeout=10,
        params={"limit_start": 0, "limit_page_length": total_count},
    )
    # Retry on session expiration
    if response.status_code == 403:
        print("Session expired, logging in again...")
        session = login_to_erp()
        response = session.get(
            f"{API_BASE}/api/resource/{linked_doctype}",
            headers={"Content-Type": "application/json"},
            timeout=10,
            params={"limit_start": 0, "limit_page_length": total_count},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch link options for '{linked_doctype}': {response.text}",
        )

    data = response.json().get("data")
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found for DocType: {linked_doctype}")

    return data

def fetch_link_options_count(linked_doctype: str):
    """Fetches the total count of records for a linked_doctype without fetching all data."""
    session = login_to_erp()
    # Use the count function with filters to get the exact count matching the filters
    total_count = get_doctype_count(session, linked_doctype)
    return {"total_count": total_count}