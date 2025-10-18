from fastapi import HTTPException
from typing import Dict, Any
import requests
from pydantic import BaseModel
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from .login import login_to_erp

load_dotenv()


class SubmissionItem(BaseModel):
    id: str
    formName: str
    data: Dict[str, Any]
    schemaHash: str
    status: str  # 'pending' | 'submitted' | 'failed'

API_BASE = os.getenv("API_BASE")
SUBMISSION_ENDPOINT = f'{API_BASE}/api/resource/'

async def send_submission_to_server(form_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Send the submission data to the server"""
    try:
        if not form_name or not data:
            raise HTTPException(status_code=400, detail="Form name and data are required")
        
        session = login_to_erp()
        
        endpoint_url = f"{SUBMISSION_ENDPOINT}{form_name}"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Expect': ''  # Disable Expect header that might cause 417
        }
        
        response = session.post(
            endpoint_url,
            json=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            return response_data
        else:   
            raise HTTPException(
                status_code=response.status_code,
                detail={
                    'success': False,
                    'error': 'Failed to submit data to server',
                    'status_code': response.status_code,
                    'response_body': response.text
                }
            )
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error during submission - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': f'Network error during submission: {str(e)}'
            }
        )
