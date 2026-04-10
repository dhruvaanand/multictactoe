from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from backend.database import get_mysql_pool
from backend.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mysql = await get_mysql_pool()
    yield
    app.state.mysql.close()
    await app.state.mysql.wait_closed()

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")