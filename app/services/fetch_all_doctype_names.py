from fastapi import HTTPException
from typing import Dict, Any
import requests
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from .login import login_to_erp
from .fetchDoctype import fetch_doctype

load_dotenv()

API_BASE = os.getenv("API_BASE")
ERP_USER = os.getenv("ERP_USER", "ads@aegiondynamic.com")
ERP_PASS = os.getenv("ERP_PASS", "Csa@2025")

def has_link_field(doctype_data: Dict[str, Any]) -> bool:
    """Check if a doctype has any field with type 'Link'"""
    fields = doctype_data.get("fields", [])
    for field in fields:
        if field.get("fieldtype") == "Link":
            return True
    return False

def fetch_all_doctype_names() -> List[Dict[str, Any]]:
    """Logs in and fetches all DocType names, excluding those with Link fields."""
    session = login_to_erp()
    response = session.get(
        f"{API_BASE}/api/resource/DocType?limit=1000",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if response.status_code == 403:
        print("Session expired, logging in again...")
        session = login_to_erp()
        response = session.get(f"{API_BASE}/api/resource/DocType")

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch DocTypes: {response.text}",
        )
    
    data = response.json().get("data")
    if not data:
        raise HTTPException(status_code=404, detail="No DocTypes found")

    # Filter out doctypes that have Link fields
    filtered_doctypes = []
    for doctype in data:
        doctype_name = doctype.get("name")
        try:
            # Fetch the full doctype details
            doctype_details = fetch_doctype(doctype_name)
            
            # Only include if it doesn't have Link fields
            if not has_link_field(doctype_details):
                filtered_doctypes.append(doctype)
        except Exception as e:
            # If there's an error fetching a specific doctype, skip it
            print(f"Error fetching doctype '{doctype_name}': {str(e)}")
            continue

    return filtered_doctypes