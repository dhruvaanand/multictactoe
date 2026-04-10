import aiomysql
from motor.motor_asyncio import AsyncIOMotorClient

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "root",
    "db": "multictactoe",
}

MONGO_URL = "mongodb://localhost:27017"

mongo_client = AsyncIOMotorClient(MONGO_URL)
mongo_db = mongo_client["multictactoe"]

async def get_mysql_pool():
    return await aiomysql.create_pool(**MYSQL_CONFIG, minsize=5, maxsize=20)