from fastapi import Header, HTTPException
from .config import settings


async def enforce_bearer_auth(authorization: str | None = Header(default=None)):
    if settings.API_AUTH_TOKEN is None:
        return  # open for local prototyping
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.API_AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")