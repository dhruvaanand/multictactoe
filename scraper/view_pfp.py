import base64
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def view():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    doc = await client["multictactoe"]["images"].find_one({"uid":"2025101011"})
    img_bytes = base64.b64decode(doc["image"])
    with open("test_pfp.jpg", "wb") as f:
        f.write(img_bytes)
    print(f"Saved: {doc['uid']}")
    client.close()

asyncio.run(view())