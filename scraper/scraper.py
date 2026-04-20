import asyncio
import csv
import base64
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
import aiomysql

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "root",
    "db": "multictactoe",
}

MONGO_URL = "mongodb://localhost:27017"
SEMAPHORE = asyncio.Semaphore(20)

async def fetch_image(client: httpx.AsyncClient, url: str) -> bytes | None:
    try:
        async with SEMAPHORE:
            r = await client.get(url, timeout=10)
            if r.status_code == 200:
                return r.content
            return None
    except Exception:
        return None

async def insert_mysql(pool, uid: str, name: str):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO users (uid, name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name=%s",
                (uid, name, name)
            )
        await conn.commit()

async def upsert_mongo(collection, uid: str, image: bytes):
    encoded = base64.b64encode(image).decode()
    await collection.update_one(
        {"uid": uid},
        {"$set": {"uid": uid, "image": encoded}},
        upsert=True
    )

async def process_student(client, pool, mongo_col, uid, name, url):
    image = await fetch_image(client, f"https://{url}/images/pfp.jpg")
    if image is None:
        print(f"FAIL  {uid} — image not found")
        return False


    await asyncio.gather(
        insert_mysql(pool, uid, name),
        upsert_mongo(mongo_col, uid, image)
    )
    print(f"OK    {uid}")
    return True

async def main():
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    mongo_col = mongo_client["multictactoe"]["images"]

    pool = await aiomysql.create_pool(**MYSQL_CONFIG, minsize=5, maxsize=20)

    with open("batch_data.csv") as f:
        students = list(csv.DictReader(f))

    async with httpx.AsyncClient() as client:
        tasks = [
            process_student(client, pool, mongo_col,
                          s["uid"], s["name"], s["website_url"])
            for s in students
        ]
        outcomes = await asyncio.gather(*tasks)

    results = {"ok": sum(outcomes), "fail": len(outcomes) - sum(outcomes)}
    print(f"\nDone — {results['ok']} succeeded, {results['fail']} failed")
    pool.close()
    await pool.wait_closed()
    mongo_client.close()

if __name__ == "__main__":
    asyncio.run(main())