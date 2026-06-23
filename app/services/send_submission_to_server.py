from fastapi import HTTPException
from typing import Dict, Any
import requests
from pydantic import BaseModel
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from .login import login_to_erp, invalidate_session, get_user_erp_session, invalidate_user_session

load_dotenv()


class SubmissionItem(BaseModel):
    id: str
    formName: str
    data: Dict[str, Any]
    schemaHash: str
    status: str  # 'pending' | 'submitted' | 'failed'
    is_submittable: int

API_BASE = os.getenv("API_BASE")
SUBMISSION_ENDPOINT = f'{API_BASE}/api/resource/'

ERP_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Expect': '',
}


def _extract_erp_error(response: requests.Response) -> str | None:
    """Extract a clean user-facing error message from a Frappe error response."""
    try:
        body = response.json()
        # _server_messages has the cleanest user-facing text
        raw = body.get('_server_messages')
        if raw:
            msgs = json.loads(raw)
            if isinstance(msgs, list) and msgs:
                first = msgs[0]
                if isinstance(first, str):
                    first = json.loads(first)
                msg = first.get('message') if isinstance(first, dict) else None
                if msg:
                    return msg
        # Fall back to exception field (strip the exception class prefix)
        exception = body.get('exception', '')
        if exception:
            return exception.split(': ', 1)[-1].strip() or exception
        return body.get('exc_type')
    except Exception:
        return None


def _erp_post_with_retry(session_fn, invalidate_fn, url: str, *, json_body=None, timeout=30) -> requests.Response:
    """POST to ERP, retrying once on 403 with a fresh session."""
    for attempt in range(2):
        session = session_fn()
        response = session.post(url, json=json_body, headers=ERP_HEADERS, timeout=timeout)
        if response.status_code == 403 and attempt == 0:
            invalidate_fn()
            continue
        return response
    return response  # unreachable but satisfies type checkers


async def send_submission_to_server(
    form_name: str,
    is_submittable: int,
    data: Dict[str, Any],
    user_email: str | None = None,
) -> Dict[str, Any]:
    if not form_name or not data:
        raise HTTPException(status_code=400, detail="Form name and data are required")

    if user_email:
        try:
            get_user_erp_session(user_email)  # warm cache; raises on ERP permission/user issues
            session_fn = lambda: get_user_erp_session(user_email)
            invalidate_fn = lambda: invalidate_user_session(user_email)
        except Exception as e:
            print(f"[ERP] Per-user session failed for {user_email}: {e}. Falling back to service account.")
            session_fn = login_to_erp
            invalidate_fn = invalidate_session
    else:
        session_fn = login_to_erp
        invalidate_fn = invalidate_session

    try:
        create_response = _erp_post_with_retry(
            session_fn,
            invalidate_fn,
            f"{SUBMISSION_ENDPOINT}{form_name}",
            json_body=data,
        )

        if create_response.status_code != 200:
            erp_error = _extract_erp_error(create_response)
            print(f"ERP create error [{create_response.status_code}]: {create_response.text[:500]}")
            raise HTTPException(
                status_code=create_response.status_code,
                detail={
                    'success': False,
                    'error': erp_error or 'Failed to create record',
                    'response_body': create_response.text,
                }
            )

        if is_submittable == 0:
            return create_response.json()

        doc_name = create_response.json().get("data", {}).get("name")
        submit_response = _erp_post_with_retry(
            session_fn,
            invalidate_fn,
            f"{SUBMISSION_ENDPOINT}{form_name}/{doc_name}?run_method=submit",
        )

        if submit_response.status_code != 200:
            erp_error = _extract_erp_error(submit_response)
            print(f"ERP submit error [{submit_response.status_code}]: {submit_response.text[:500]}")
            raise HTTPException(
                status_code=submit_response.status_code,
                detail={
                    'success': False,
                    'error': erp_error or 'Failed to submit record',
                    'response_body': submit_response.text,
                }
            )

        return submit_response.json()

    except requests.exceptions.RequestException as e:
        print(f"Network error during submission: {e}")
        raise HTTPException(
            status_code=500,
            detail={'success': False, 'error': f'Network error: {str(e)}'}
        )