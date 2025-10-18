import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Literal
from services.fetchDoctype import fetch_doctype
from services.fetch_all_doctype_names import fetch_all_doctype_names
from services.send_submission_to_server import send_submission_to_server
from services.create_schema_hash import create_schema_hash

class SubmissionItem(BaseModel):
    id: str
    formName: str
    data: Dict[str, Any]
    schemaHash: str
    status: Literal['pending', 'submitted', 'failed']

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ERP_SYSTEMS = [
    {"id": 1, "name": "ERP 1", "formCount": 15},
    {"id": 2, "name": "ERP 2", "formCount": 15},
    {"id": 3, "name": "ERP 3", "formCount": 15},
    {"id": 4, "name": "ERP 4", "formCount": 15},
    {"id": 5, "name": "ERP 5", "formCount": 15},
    {"id": 6, "name": "ERP 6", "formCount": 15},
]

@app.get("/api/erp-systems")
async def get_erp_systems():
    return ERP_SYSTEMS

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

@app.get("/doctype/{form_name}")
def get_doctype(form_name: str):
    data = fetch_doctype(form_name)
    return {"data": data}

@app.get("/doctype")
def get_all_doctypes():
    data = fetch_all_doctype_names()
    return {"data": data}


# @app.post("/submit/{form_name}")
# async def submit_form(form_name: str, data: Dict[str, Any]):
#     response = await send_submission_to_server(form_name, data)
#     return response

@app.post("/submit")
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
        else:
            response = await send_submission_to_server(submission_item.formName, submission_item.data)
            return response
        
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
