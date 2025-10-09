from fastapi import HTTPException
from typing import Dict, Any
import requests
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from .login import login_to_erp

load_dotenv()

API_BASE = os.getenv("API_BASE")
ERP_USER = os.getenv("ERP_USER", "ads@aegiondynamic.com")
ERP_PASS = os.getenv("ERP_PASS", "Csa@2025")

def fetch_all_doctype_names() -> List[Dict[str, Any]]:
    """Logs in and fetches all DocType names."""
    session = login_to_erp()
    response = session.get(
        f"{API_BASE}/api/resource/DocType",
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

    return data