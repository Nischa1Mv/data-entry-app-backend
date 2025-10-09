from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.services.fetchDoctype import fetch_doctype
from app.services.send_submission_to_server import send_submission_to_server
from app.services.create_schema_hash import create_schema_hash
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()

class SubmissionItem(BaseModel):
    id: str
    formName: str
    data: Dict[str, Any]
    schemaHash: str
    status: str  # 'pending' | 'submitted' | 'failed'

API_BASE = os.getenv("API_BASE")
DOCTYPE_ENDPOINT = f'{API_BASE}/api/doctype/'
SUBMISSION_ENDPOINT = f'{API_BASE}/api/submission'

@router.post("/sync")
async def sync_data(submission_item: SubmissionItem):
    try:
        # getting the doctype
        doctype_data = await fetch_doctype(submission_item.formName)
        
        # creating the hash with from the server schema
        current_schema_hash = create_schema_hash(doctype_data.get('schema', {}))
        
        # checking the hash
        if current_schema_hash != submission_item.schemaHash:
            return {
                'success': False,
                'error': 'Schema hash mismatch',
                'message': 'The form schema has been updated. Please refresh and resubmit.',
                'current_hash': current_schema_hash,
                'submitted_hash': submission_item.schemaHash
            }
        
        # post the form data to server
        server_response = await send_submission_to_server(submission_item)
        
        return {
            'success': True,
            'message': 'Data synced successfully',
            'submission_id': submission_item.id,
            'server_response': server_response
        }
            
    except HTTPException:
        # Re-raise HTTPExceptions as they are already properly formatted
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': f'Internal error: {str(e)}'
            }
        )