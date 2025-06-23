import os
import logging
import aiohttp
import datetime
import asyncio
from pathlib import Path
from src.db.mongo import get_database

BASE_DIR = Path(__file__).resolve().parent  # src/search-by-image
IMAGE_DIR = BASE_DIR / "data"
os.makedirs(IMAGE_DIR, exist_ok=True)

logger = logging.getLogger(__name__)
db = get_database()
meals_collection = db["meals"]

def get_image_filename(meal_id):
    return os.path.join(IMAGE_DIR, f"meal_{meal_id}.jpg")

async def fetch_image_urls():
    query = {"updatedAt": {"$gt": datetime.datetime.utcnow() - datetime.timedelta(days=365)}}
    projection = {"_id": 1, "images": 1}
    urls = []

    async for doc in meals_collection.find(query, projection).limit(50):  # Limit added
        for img in doc.get("images", []):
            url = img.get("secure_url")
            if url:
                urls.append((str(doc["_id"]), url))
    logger.info(f"Fetched {len(urls)} image URLs")
    return urls

async def download_image(session, url, filename):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(filename, 'wb') as f:
                    f.write(await resp.read())
                return True
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
    return False

async def download_images(image_data):
    timeout = aiohttp.ClientTimeout(total=30)  # Timeout added
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = []
        for meal_id, url in image_data:
            filename = get_image_filename(meal_id)
            if not os.path.exists(filename):
                tasks.append(download_image(session, url, filename))
        await asyncio.gather(*tasks)
