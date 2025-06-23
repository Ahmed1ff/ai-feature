import os
import shutil
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from DeepImageSearch import Load_Data, Search_Setup
import builtins
from src.search_by_image.image_utils import fetch_image_urls, download_images

# Override built-in input to auto-confirm
builtins.input = lambda *args, **kwargs: "yes"

# Set working directory
os.chdir(Path(__file__).resolve().parent)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "data"
UPLOAD_FOLDER = BASE_DIR / "uploads"
Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

search_engine = None

async def update_index_with_new_images():
    image_data = await fetch_image_urls()
    await download_images(image_data)
    image_list = Load_Data().from_folder([IMAGE_DIR])
    if search_engine:
        search_engine.run_index()

async def initialize_search_engine():
    global search_engine

    # Delete existing index if it exists
    if os.path.exists('.deep_image_search'):
        shutil.rmtree('.deep_image_search')

    try:
        logger.info("Fetching image URLs from DB...")
        image_data = await fetch_image_urls()
        await download_images(image_data)

        image_list = Load_Data().from_folder([IMAGE_DIR])
        logger.info(f"Total images indexed: {len(image_list)}")

        if not image_list:
            logger.warning("No images found to index.")
            return

        search_engine = Search_Setup(image_list=image_list)
        search_engine.run_index()
        logger.info("Search engine initialized.")

        asyncio.create_task(update_index_with_new_images())

    except Exception as e:
        logger.error(f"Error initializing search engine: {e}")

# Create the FastAPI app
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(initialize_search_engine())

@app.get("/")
def home():
    return {"message": "FastAPI is running with image search!"}

@app.post("/search-by-image/")
async def search_by_image(file: UploadFile = File(...), top_n: int = 5):
    file_location = f"{UPLOAD_FOLDER}/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if search_engine is None:
        logger.warning("Search engine not initialized. No data available for search.")
        raise HTTPException(
            status_code=503,
            detail="Search engine not initialized. No data available for search."
        )

    search_results = search_engine.get_similar_images(
        image_path=file_location, number_of_images=top_n
    )
    meal_ids = []
    for path in search_results.values():
        filename = os.path.basename(path)
        if filename.startswith("meal_") and filename.endswith(".jpg"):
            meal_id = filename.replace("meal_", "").replace(".jpg", "")
            meal_ids.append(meal_id)

    return {
        "query_image": file_location,
        "similar_meal_ids": meal_ids
    }
