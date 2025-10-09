import requests
import os
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE")
ERP_USER = os.getenv("ERP_USER")
ERP_PASS = os.getenv("ERP_PASS")

SESSION_COOKIES = None

def login_to_erp() -> requests.Session:
    """Logs in once and returns a session with cookies."""
    global SESSION_COOKIES

    session = requests.Session()

    if SESSION_COOKIES:
        session.cookies.update(SESSION_COOKIES)
        return session

    response = session.post(
        f"{API_BASE}/api/method/login",
        json={"usr": ERP_USER, "pwd": ERP_PASS},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="ERP login failed")

    SESSION_COOKIES = session.cookies.get_dict()

    return session
