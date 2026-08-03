import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, APIKeyHeader

from app.core.config import settings
from app.core.logger import logger

# --- API Token Security ---
# We accept either "X-API-Key" or standard "Authorization: Bearer <TOKEN>"
# We'll just define APIKeyHeader and fallback logic if needed, but typically X-API-Key is simpler.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_token(api_key: str = Depends(api_key_header)):
    """
    Dependency to verify API Token for endpoints.
    Accepts token via X-API-Key header.
    """
    if not api_key:
        logger.warning("Attempted access without API key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API token",
        )
    
    # Use secrets.compare_digest to prevent timing attacks
    if not secrets.compare_digest(api_key, settings.api_token):
        logger.warning("Attempted access with invalid API key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API token",
        )
    return api_key


# --- Swagger UI Basic Auth ---
security_basic = HTTPBasic()

def verify_docs_auth(credentials: HTTPBasicCredentials = Depends(security_basic)):
    """
    Dependency to verify HTTP Basic Auth for Swagger/ReDoc pages.
    """
    correct_username = secrets.compare_digest(credentials.username, settings.docs_username)
    correct_password = secrets.compare_digest(credentials.password, settings.docs_password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
