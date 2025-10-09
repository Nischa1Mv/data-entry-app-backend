# app/services/fetch_doctype.py
from fastapi import HTTPException
from typing import Dict, Any
import requests
import os
from .login import login_to_erp
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE")
LOGIN_ENDPOINT = f"{API_BASE}/api/method/login"
DOCTYPE_ENDPOINT = f"{API_BASE}/api/resource/DocType"

ERP_USER = os.getenv("ERP_USER", "ads@aegiondynamic.com")
ERP_PASS = os.getenv("ERP_PASS", "Csa@2025")

def fetch_doctype(form_name: str) -> Dict[str, Any]:
    """Logs into ERPNext and fetches a given DocType."""
    with requests.Session() as session:
        try:
            session = login_to_erp()
            response = session.get(
                f"{DOCTYPE_ENDPOINT}/{form_name}",
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch DocType '{form_name}': {response.text}",
                )

            data = response.json()
            if not data.get("data"):
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for DocType: {form_name}",
                )

            return data["data"]

        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="Request timed out")

        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500, detail=f"Network error while fetching DocType: {str(e)}"
            )
