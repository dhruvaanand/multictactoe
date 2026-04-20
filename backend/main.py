from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from backend.database import get_mysql_pool
from backend.auth import router as auth_router
from backend.lobby import router as lobby_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mysql = await get_mysql_pool()
    yield
    app.state.mysql.close()
    await app.state.mysql.wait_closed()

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(lobby_router)

@app.get("/")
async def root():
    return RedirectResponse(url="/login.html")

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")