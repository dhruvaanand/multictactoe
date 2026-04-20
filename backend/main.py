import asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from backend.database import get_mysql_pool, mongo_db
from backend.auth import router as auth_router
from backend.lobby import router as lobby_router
from backend.game import router as game_router
from utils.facial_recognition_module import build_encodings_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mysql = await get_mysql_pool()
    app.state.encodings_cache = await rebuild_encodings_cache()
    yield
    app.state.mysql.close()
    await app.state.mysql.wait_closed()


async def rebuild_encodings_cache():
    db_images_dict = {}
    async for doc in mongo_db.images.find({}):
        db_images_dict[doc["uid"]] = doc["image"]
    return await asyncio.to_thread(build_encodings_cache, db_images_dict)

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(lobby_router)
app.include_router(game_router)

@app.get("/")
async def root():
    return RedirectResponse(url="/login.html")


@app.get("/leaderboard")
async def leaderboard(request: Request):
    mysql_pool = request.app.state.mysql
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT uid, name, elo_rating, is_online FROM users ORDER BY elo_rating DESC, uid ASC"
            )
            rows = await cur.fetchall()

    return [
        {
            "uid": row[0],
            "name": row[1],
            "elo": row[2],
            "is_online": bool(row[3]),
        }
        for row in rows
    ]


@app.post("/admin/rebuild-encodings")
async def admin_rebuild_encodings(request: Request):
    request.app.state.encodings_cache = await rebuild_encodings_cache()
    return {"status": "ok", "cache_size": len(request.app.state.encodings_cache)}

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")