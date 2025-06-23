from fastapi import FastAPI

main_app = FastAPI()

@main_app.get("/")
def read_root():
    return {"message": "Hello from Azure! This is a simple test."}
