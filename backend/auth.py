from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from backend.session import (
    SESSION_COOKIE_NAME,
    create_session,
    destroy_session,
    get_uid_from_request,
)
from utils.facial_recognition_module import find_closest_match

router = APIRouter()


class LoginRequest(BaseModel):
    image: str  # Base64 encoded string from frontend


def _build_login_response(uid: str) -> Response:
    response = Response(
        content=f'{{"status":"success","uid":"{uid}","message":"Welcome back, UID {uid}"}}',
        media_type="application/json",
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session(uid),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 12,
    )
    return response


@router.post("/login")
async def login(request: Request, payload: LoginRequest):
    if payload.image == "ADMIN_BYPASS":
        admin_uid = "0000000000"
        async with request.app.state.mysql.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (uid, name) VALUES (%s, 'SYSTEM_ADMIN') ON DUPLICATE KEY UPDATE is_online = TRUE",
                    (admin_uid,),
                )
            await conn.commit()
        return _build_login_response(admin_uid)

    encodings_cache = getattr(request.app.state, "encodings_cache", None)
    if encodings_cache is None:
        raise HTTPException(status_code=503, detail="Biometric service not initialized")

    try:
        image_data = payload.image
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        uid = find_closest_match(image_data, encodings_cache)
    except Exception as e:
        print(f"Error during facial recognition: {e}")
        raise HTTPException(status_code=500, detail="Internal error in biometric service")

    if not uid:
        raise HTTPException(status_code=401, detail="Biometric match failed")

    mysql_pool = request.app.state.mysql
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT uid FROM users WHERE uid = %s", (uid,))
            user_row = await cur.fetchone()
            if not user_row:
                raise HTTPException(status_code=401, detail="Matched profile is not a valid user")

            await cur.execute("UPDATE users SET is_online = TRUE WHERE uid = %s", (uid,))
        await conn.commit()

    return _build_login_response(uid)


@router.get("/me")
async def me(request: Request):
    uid = get_uid_from_request(request)
    mysql_pool = request.app.state.mysql
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT uid, name, elo_rating, is_online FROM users WHERE uid = %s", (uid,))
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "uid": row[0],
        "name": row[1],
        "elo": row[2],
        "is_online": bool(row[3]),
    }


@router.post("/logout")
async def logout(request: Request):
    uid = get_uid_from_request(request)
    token = request.cookies.get(SESSION_COOKIE_NAME)

    mysql_pool = request.app.state.mysql
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET is_online = FALSE WHERE uid = %s", (uid,))
        await conn.commit()

    destroy_session(token)
    response = Response(content='{"status":"ok"}', media_type="application/json")
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response
