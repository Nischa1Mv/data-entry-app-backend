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
    is_submittable: int

API_BASE = os.getenv("API_BASE")
SUBMISSION_ENDPOINT = f'{API_BASE}/api/resource/'

async def send_submission_to_server(form_name: str,is_submittable:int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Send the submission data to the server"""
    try:
        if not form_name or not data:
            raise HTTPException(status_code=400, detail="Form name and data are required")
        
        session = login_to_erp()
        
        create_url = f"{SUBMISSION_ENDPOINT}{form_name}"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Expect': ''  # Disable Expect header that might cause 417

        }

        create_response = session.post(create_url,json=data,headers=headers,timeout=30)
        if(create_response.status_code!=200):
            raise HTTPException(
                status_code=create_response.status_code,
                detail={
                    'success': False,
                    'error': 'Failed to create record',
                    'status_code': create_response.status_code,
                    'response_body': create_response.text
                }
            )
        
        # If is_submittable is 0, only create the record and return
        if is_submittable == 0:
            return create_response.json()
        
        # If is_submittable is 1, proceed to submit the record
        doc_name=create_response.json().get("data", {}).get("name")

        submit_url=f"{SUBMISSION_ENDPOINT}{form_name}/{doc_name}?run_method=submit"
        submit_response = session.post(submit_url,headers=headers,timeout=30)
        if(submit_response.status_code!=200):
            raise HTTPException(
                status_code=submit_response.status_code,
                detail={
                    'success': False,
                    'error': 'Failed to submit record',
                    'status_code': submit_response.status_code,
                    'response_body': submit_response.text
                }
            )
        return submit_response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error during submission - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': f'Network error during submission: {str(e)}'
            }
        )