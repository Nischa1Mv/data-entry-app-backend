import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Literal
from services.fetchDoctype import fetch_doctype
from services.fetch_all_doctype_names import fetch_all_doctype_names
from services.send_submission_to_server import send_submission_to_server
from services.create_schema_hash import create_schema_hash
from middleware.auth_middleware import AuthMiddleware
from utils.auth_utils import get_current_token, require_auth, get_current_user_info, get_current_user_email
from services.fetch_link_options import fetch_link_options, fetch_link_options_count

class SubmissionItem(BaseModel):
    id: str
    formName: str
    data: Dict[str, Any]
    schemaHash: str
    status: Literal['pending', 'submitted', 'failed']
    is_submittable: int

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
# You can configure which routes to protect by specifying protected_routes
# If protected_routes is empty or None, all routes will be protected
app.add_middleware(
    AuthMiddleware,
    protected_routes=["/api", "/doctype", "/link-options", "/submit"],  # Only protect these routes
    # protected_routes=None,  # Uncomment this line to protect ALL routes
    auth_header="Authorization",
    token_prefix="Bearer "
)

ERP_SYSTEMS = [
    {"id": 1, "name": "CSA", "formCount": 3},
    {"id": 2, "name": "Sahaja Aharam", "formCount": 0},
    {"id": 3, "name": "FPO Hub", "formCount": 0},
]

@app.get("/api/erp-systems", operation_id="get_erp_systems")
async def get_erp_systems():
    return ERP_SYSTEMS

@app.get("/doctype/{form_name}", operation_id="get_doctype_by_name")
def get_doctype(form_name: str):
    data = fetch_doctype(form_name)
    return {"data": data}

@app.get("/doctype", operation_id="get_all_doctypes")
def get_all_doctypes():
    data = fetch_all_doctype_names(limit_start=0, limit_page_length=1000)
    return {"data": data}

@app.get("/link-options/{linked_doctype}/count", operation_id="get_link_options_count")
def get_link_options_count(linked_doctype: str):
    """Get the total count of records for a linked_doctype."""
    result = fetch_link_options_count(linked_doctype)
    return result

@app.get("/link-options/{linked_doctype}", operation_id="get_link_options")
def get_link_options(linked_doctype: str):
    data = fetch_link_options(linked_doctype)
    return {"data": data}

#for postman testing
# @app.post("/submit/{form_name}")
# async def submit_form(form_name: str, data: Dict[str, Any]):
#     response = await send_submission_to_server(form_name, data)
#     return response

@app.post("/submit", operation_id="submit_form_data")
async def submit_single_form(submission_item: SubmissionItem):
    try:
        # getting the doctype
        doctype_data = fetch_doctype(submission_item.formName)
        # creating the hash from the server schema
        latest_schema_hash = create_schema_hash(doctype_data)
        
        if latest_schema_hash != submission_item.schemaHash:
            raise HTTPException(
                status_code=400,
                detail={
                    'success': False,
                    'error': 'Schema hash mismatch',
                    'message': 'The form schema has been updated. Please refresh and resubmit.',
                    'latest_schema_hash': latest_schema_hash,
                    'schemaHash': submission_item.schemaHash
                }
            )
        response = await send_submission_to_server(submission_item.formName,submission_item.is_submittable,submission_item.data )
        return {
            'success': True,
            'message': 'Form submitted successfully',
            'form_name': submission_item.formName,
            'submission_id': submission_item.id,
            'data': submission_item.data,
            'server_response': response
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle other exceptions
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': 'Internal server error',
                'message': str(e)
            }
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
