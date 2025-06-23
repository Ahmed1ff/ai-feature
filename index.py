from fastapi import FastAPI
from src.search_by_image.search import app as search_app  # removed lifespan

main_app = FastAPI()

# Mount the inner app under a prefix
@main_app.get("/")
def read_root():
    return {"message": "Hello from Azure!"}
# Command to run:
# uvicorn index:main_app --host 0.0.0.0 --port 8000
