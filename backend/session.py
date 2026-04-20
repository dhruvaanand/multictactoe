import secrets
from typing import Optional

from fastapi import HTTPException, Request, WebSocket


# In-memory session storage.
# token -> uid
_sessions: dict[str, str] = {}


SESSION_COOKIE_NAME = "arena_session"


def create_session(uid: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = uid
    return token


def get_uid_for_token(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    return _sessions.get(token)


def destroy_session(token: Optional[str]) -> None:
    if token and token in _sessions:
        del _sessions[token]


def get_uid_from_request(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    uid = get_uid_for_token(token)
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return uid


def get_uid_from_websocket(websocket: WebSocket) -> str:
    token = websocket.cookies.get(SESSION_COOKIE_NAME)
    uid = get_uid_for_token(token)
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return uid
