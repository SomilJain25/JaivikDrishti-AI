import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

load_dotenv()

API_KEY=os.getenv("API_KEY")

api_key_header=APIKeyHeader(
    name="X-API-Key"
)

def verify_api_key(
    api_key:str=Depends(api_key_header)
):

    if api_key!=API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return api_key