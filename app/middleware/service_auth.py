import os
from fastapi import Header, HTTPException

AI_SERVICE_SECRET = os.getenv("AI_SERVICE_SECRET")

def verify_ai_service(
    x_ai_service_key: str = Header(...)
):
    if x_ai_service_key != AI_SERVICE_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Forbidden"
        )