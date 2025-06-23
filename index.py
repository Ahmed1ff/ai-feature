from fastapi import FastAPI
from src.search_by_image.search import app as search_app  # removed lifespan

main_app = FastAPI()

# Mount the inner app under a prefix
main_app.mount("/search", search_app)

# Root-level route for testing
@main_app.get("/")
def root():
    return {"message": "Main App is running"}

# Command to run:
# uvicorn index:main_app --host 0.0.0.0 --port 8000
