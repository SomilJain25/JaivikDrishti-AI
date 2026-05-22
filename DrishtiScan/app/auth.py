import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

load_dotenv()

API_KEY=os.getenv("API_KEY")

api_key_header=APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)

def verify_api_key(
    api_key: Optional[str] = Depends(api_key_header)
):
    if not API_KEY:
        return None

    if api_key!=API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return api_key
