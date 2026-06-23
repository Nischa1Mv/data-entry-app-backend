from .login import login_to_erp
import os
import json
import requests
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()

API_BASE = os.getenv("API_BASE")

def get_doctype_count(
    session: requests.Session,
    linked_doctype: str,
    filters: str | None = None,
) -> int:
    """Fetches the total count of documents matching the filters."""
    COUNT_ENDPOINT = f"{API_BASE}/api/method/frappe.client.get_count"

    count_params: dict = {"doctype": linked_doctype}
    if filters:
        count_params["filters"] = filters

    count_response = session.get(COUNT_ENDPOINT, params=count_params, timeout=10)
    if count_response.status_code == 200:
        try:
            return int(count_response.json().get("message", 0))
        except (ValueError, json.JSONDecodeError):
            print("Warning: Could not parse count response. Defaulting to 1000 limit.")
            return 1000
    else:
        print(f"Warning: Failed to get count ({count_response.status_code}). Defaulting to 1000 limit.")
        return 1000


def fetch_link_options(
    linked_doctype: str,
    filter_field: str | None = None,
    filter_value: str | None = None,
):
    session = login_to_erp()

    filters: str | None = None
    if filter_field and filter_value:
        filters = json.dumps([[linked_doctype, filter_field, "=", filter_value]])

    total_count = get_doctype_count(session, linked_doctype, filters=filters)
    if total_count <= 0:
        return []

    fetch_params: dict = {"limit_start": 0, "limit_page_length": total_count}
    if filters:
        fetch_params["filters"] = filters

    response = session.get(
        f"{API_BASE}/api/resource/{linked_doctype}",
        headers={"Content-Type": "application/json"},
        timeout=10,
        params=fetch_params,
    )
    if response.status_code == 403:
        print("Session expired, logging in again...")
        session = login_to_erp()
        response = session.get(
            f"{API_BASE}/api/resource/{linked_doctype}",
            headers={"Content-Type": "application/json"},
            timeout=10,
            params=fetch_params,
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


def fetch_link_options_count(
    linked_doctype: str,
    filter_field: str | None = None,
    filter_value: str | None = None,
):
    """Fetches the total count of records for a linked_doctype without fetching all data."""
    session = login_to_erp()

    filters: str | None = None
    if filter_field and filter_value:
        filters = json.dumps([[linked_doctype, filter_field, "=", filter_value]])

    total_count = get_doctype_count(session, linked_doctype, filters=filters)
    return {"total_count": total_count}