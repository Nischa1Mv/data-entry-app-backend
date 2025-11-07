from .login import login_to_erp
import os
import json
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()

API_BASE = os.getenv("API_BASE")

def fetch_link_options(linked_doctype: str):
    session = login_to_erp()
    response = session.get(
        f"{API_BASE}/api/resource/{linked_doctype}",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    # Retry on session expiration
    if response.status_code == 403:
        print("Session expired, logging in again...")
        session = login_to_erp()
        response = session.get(
            f"{API_BASE}/api/resource/{linked_doctype}",
            headers={"Content-Type": "application/json"},
            timeout=10,
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