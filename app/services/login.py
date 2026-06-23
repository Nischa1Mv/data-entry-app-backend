import requests
import os
import sqlite3
from typing import Dict
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE")
ERP_USER = os.getenv("ERP_USER")
ERP_PASS = os.getenv("ERP_PASS")

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "user_erp_keys.db")

SESSION_COOKIES = None
_user_sessions: Dict[str, requests.Session] = {}

_ERP_JSON_HEADER = {"Content-Type": "application/json"}


def _init_db():
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_erp_credentials (
                email TEXT PRIMARY KEY,
                api_key TEXT NOT NULL,
                api_secret TEXT NOT NULL
            )
        """)

_init_db()


def _load_stored_credentials(email: str):
    with sqlite3.connect(_DB_PATH) as conn:
        row = conn.execute(
            "SELECT api_key, api_secret FROM user_erp_credentials WHERE email = ?", (email,)
        ).fetchone()
    return (row[0], row[1]) if row else None


def _store_credentials(email: str, api_key: str, api_secret: str):
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_erp_credentials (email, api_key, api_secret) VALUES (?, ?, ?)",
            (email, api_key, api_secret),
        )


def invalidate_session():
    global SESSION_COOKIES
    SESSION_COOKIES = None


def login_to_erp() -> requests.Session:
    """Service-account login. Cached globally; used for read-only ERP calls."""
    global SESSION_COOKIES

    session = requests.Session()

    if SESSION_COOKIES:
        session.cookies.update(SESSION_COOKIES)
        return session

    response = session.post(
        f"{API_BASE}/api/method/login",
        json={"usr": ERP_USER, "pwd": ERP_PASS},
        headers=_ERP_JSON_HEADER,
        timeout=10,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="ERP login failed")

    SESSION_COOKIES = session.cookies.get_dict()
    return session


def _build_token_session(api_key: str, api_secret: str) -> requests.Session:
    session = requests.Session()
    session.headers["Authorization"] = f"Token {api_key}:{api_secret}"
    return session


def get_user_erp_session(email: str) -> requests.Session:
    """Return a per-user ERP session authenticated via Token auth.

    Checks the in-memory cache first, then the local DB, then provisions
    fresh credentials via the ERP admin account.
    """
    if email in _user_sessions:
        return _user_sessions[email]

    # Try credentials persisted in the local DB from a previous provisioning
    stored = _load_stored_credentials(email)
    if stored:
        api_key, api_secret = stored
        session = _build_token_session(api_key, api_secret)
        _user_sessions[email] = session
        return session

    # Provision new credentials via the service account
    admin = login_to_erp()

    gen_resp = admin.post(
        f"{API_BASE}/api/method/frappe.core.doctype.user.user.generate_keys",
        json={"user": email},
        headers=_ERP_JSON_HEADER,
        timeout=10,
    )
    if gen_resp.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail=f"ERP could not generate token for {email}: {gen_resp.text[:200]}",
        )
    api_secret = gen_resp.json().get("message", {}).get("api_secret")

    # Fetch the stable api_key from the User document
    user_resp = admin.get(
        f"{API_BASE}/api/resource/User/{email}",
        headers=_ERP_JSON_HEADER,
        timeout=10,
    )
    if user_resp.status_code != 200:
        raise HTTPException(status_code=401, detail=f"ERP user not found: {email}")
    api_key = user_resp.json().get("data", {}).get("api_key")

    if not api_key or not api_secret:
        raise HTTPException(
            status_code=401,
            detail=f"Failed to obtain ERP API credentials for {email}",
        )

    _store_credentials(email, api_key, api_secret)
    session = _build_token_session(api_key, api_secret)
    _user_sessions[email] = session
    return session


def invalidate_user_session(email: str):
    _user_sessions.pop(email, None)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("DELETE FROM user_erp_credentials WHERE email = ?", (email,))


def user_exists_in_erp(email: str) -> bool:
    admin = login_to_erp()
    resp = admin.get(
        f"{API_BASE}/api/resource/User/{email}",
        headers=_ERP_JSON_HEADER,
        timeout=10,
    )
    return resp.status_code == 200
