from fastapi import HTTPException
from typing import Dict, Any
import requests
from pydantic import BaseModel
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class SubmissionItem(BaseModel):
    id: str
    formName: str
    data: Dict[str, Any]
    schemaHash: str
    status: str  # 'pending' | 'submitted' | 'failed'

API_BASE = os.getenv("API_BASE")
SUBMISSION_ENDPOINT = f'{API_BASE}/api/submission'

async def send_submission_to_server(submission_item: SubmissionItem) -> Dict[str, Any]:
    """Send the submission item to the server"""
    try:
        submission_data = {
            "id": submission_item.id,
            "formName": submission_item.formName,
            "data": submission_item.data,
            "schemaHash": submission_item.schemaHash,
            "status": submission_item.status
        }
        
        response = requests.post(
            SUBMISSION_ENDPOINT,
            json=submission_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail={
                    'success': False,
                    'error': 'Failed to submit data to server',
                    'status_code': response.status_code
                }
            )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': f'Network error during submission: {str(e)}'
            }
        )
    