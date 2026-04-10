from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from backend.database import mongo_db
from utils.facial_recognition_module import find_closest_match
import base64

router = APIRouter()

class LoginRequest(BaseModel):
    image: str  # Base64 encoded string from frontend

@router.post("/login")
async def login(request: Request, payload: LoginRequest):
    # Fetch all images from MongoDB
    cursor = mongo_db.images.find({})
    db_images_dict = {}
    async for doc in cursor:
        db_images_dict[doc["uid"]] = doc["image"]

    if not db_images_dict:
        raise HTTPException(status_code=404, detail="No profile images found in database")

    # Call find_closest_match exactly as per documentation
    # Note: The facial_recognition_module has a hardcoded threshold of 0.5.
    # While the requirement mentions 0.7, the black-box module returns None for distance > 0.5.
    try:
        # payload.image might have data:image/jpeg;base64, prefix
        image_data = payload.image
        if "," in image_data:
            image_data = image_data.split(",")[1]
            
        uid = find_closest_match(image_data, db_images_dict)
    except Exception as e:
        print(f"Error during facial recognition: {e}")
        raise HTTPException(status_code=500, detail="Internal error in biometric service")

    if uid:
        # Update MySQL is_online = TRUE
        mysql_pool = request.app.state.mysql
        async with mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET is_online = TRUE WHERE uid = %s",
                    (uid,)
                )
            await conn.commit()
        
        return {
            "status": "success",
            "uid": uid,
            "message": f"Welcome back, UID {uid}"
        }
    else:
        # Distance was likely > 0.5 (module's hard limit)
        raise HTTPException(status_code=401, detail="Biometric match failed")
