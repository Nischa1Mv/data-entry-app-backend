from fastapi import HTTPException
from typing import Dict, Any
import requests

SERVER_BASE_URL = 'https://erp.kisanmitra.net'
LOGIN_ENDPOINT = f'{SERVER_BASE_URL}/api/method/login'
DOCTYPE_ENDPOINT = f'{SERVER_BASE_URL}/api/resource/DocType'

async def fetch_doctype(form_name: str) -> Dict[str, Any]:
    session = requests.Session()
    
    try:
        login_response = session.post(
            LOGIN_ENDPOINT,
            json={
                'usr': 'ads@aegiondynamic.com',
                'pwd': 'Csa@2025'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if login_response.status_code != 200:
            raise HTTPException(
                status_code=login_response.status_code,
                detail="Authentication failed"
            )
        
        response = session.get(
            f'{DOCTYPE_ENDPOINT}/{form_name}',
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data or 'data' not in data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for doctype: {form_name}"
                )
            return data['data']
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch doctype for form '{form_name}'"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error while fetching doctype: {str(e)}"
        )
    finally:
        session.close()