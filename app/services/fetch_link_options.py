from .login import login_to_erp
import os
import json
import requests
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()

API_BASE = os.getenv("API_BASE")

def get_doctype_count(session: requests.Session, linked_doctype: str, filters: dict = None) -> int:
    """Fetches the total count of documents matching the filters."""
    # 1. Define the dedicated Frappe endpoint for counting
    COUNT_ENDPOINT = f"{API_BASE}/api/method/frappe.client.get_count"
    
    count_params = {
        "doctype": linked_doctype,
    }
    
    # Add filters if provided
    if filters:
        count_params["filters"] = json.dumps([
            [key, "=", value] for key, value in filters.items()
        ])
    
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

def fetch_link_options(linked_doctype: str, filters: dict = None):
    session = login_to_erp()

    # Get dynamic count with filters
    total_count = get_doctype_count(session, linked_doctype, filters)
    if total_count <= 0:
        raise HTTPException(status_code=404, detail=f"No data found for DocType: {linked_doctype} with filters {filters}")

    # Prepare params for /resource call
    resource_params = {
        "limit_start": 0,
        "limit_page_length": total_count,
        "fields": json.dumps(["name", "parent_territory"])  # Fetch only specific fields
    }

    if filters:
        resource_params["filters"] = json.dumps([
            [key, "=", value] for key, value in filters.items()
        ])

    response = session.get(
        f"{API_BASE}/api/resource/{linked_doctype}",
        headers={"Content-Type": "application/json"},
        timeout=10,
        params=resource_params,
    )
    # Retry on session expiration
    if response.status_code == 403:
        print("Session expired, logging in again...")
        session = login_to_erp()
        response = session.get(
            f"{API_BASE}/api/resource/{linked_doctype}",
            headers={"Content-Type": "application/json"},
            timeout=10,
            params=resource_params,
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch link options for '{linked_doctype}' with filters {filters}: {response.text}",
        )

    data = response.json().get("data")
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for DocType: {linked_doctype} with filters {filters}"
        )

    return data

def fetch_link_options_count(linked_doctype: str, filters: dict = None):
    """Fetches the total count of records for a linked_doctype without fetching all data."""
    session = login_to_erp()
    total_count = get_doctype_count(session, linked_doctype, filters)
    return {"total_count": total_count}
