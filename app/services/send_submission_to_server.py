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
SUBMISSION_ENDPOINT = f'{API_BASE}/api/resource/remove this later'

async def send_submission_to_server(submission_item: SubmissionItem) -> Dict[str, Any]:
    """Forcefully reject all submissions for testing purposes"""
    if not submission_item:
        raise HTTPException(status_code=400, detail="No submission item provided")
    
    # Force failure
    raise HTTPException(
        status_code=500,
        detail={
            'success': False,
            'error': f'Forced failure for testing form: {submission_item.formName}',
        }
    )
        # response = requests.post(
        #     SUBMISSION_ENDPOINT/{submission_item.formName},
        #     json=submission_item.data,
        #     headers={'Content-Type': 'application/json'}
        # )
        # if response.status_code == 200:
        #     return response.json()
        # else:
    #         raise HTTPException(
    #             status_code=response.status_code,
    #             detail={
    #                 'success': False,
    #                 'error': 'Failed to submit data to server',
    #                 'status_code': response.status_code
    #             }
    #         )
    # except requests.exceptions.RequestException as e:
    #     raise HTTPException(
    #         status_code=500,
    #         detail={
    #             'success': False,
    #             'error': f'Network error during submission: {str(e)}'
    #         }
    #     )
    