import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Literal
from services.fetchDoctype import fetch_doctype
from services.fetch_all_doctype_names import fetch_all_doctype_names
from services.send_submission_to_server import send_submission_to_server

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

# @app.post("/submit")
# async def submit_single_form(request: Request):
#     data = await request.json()   # read JSON body
#     submission_item = SubmissionItem(**data)
#     response = await send_submission_to_server(submission_item)
#     return response

@app.post("/submit")
async def submit_single_form(request: Request):
    data = await request.json()
    submission_item = SubmissionItem(**data)
    
    # Force failure
    # raise HTTPException(
    #     status_code=500,
    #     detail={
    #         "success": False,
    #         "formname": submission_item.formName,
    #         "error": f"Forced failure for testing form"
    #     }
    # )
    # Always return success
    return {
        "success": True,
        "message": f"Submitted successfully",
        "formName": submission_item.formName
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
