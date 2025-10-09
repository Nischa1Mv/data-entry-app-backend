from fastapi import FastAPI,HTTPException
import requests
from services.fetchDoctype import fetch_doctype
from services.fetch_all_doctype_names import fetch_all_doctype_names

app = FastAPI()

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
    data=fetch_all_doctype_names()
    return {"data": data}