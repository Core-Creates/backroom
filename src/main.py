# src/main.py
from fastapi import FastAPI
from routes.express_to_fastapi import router as items_router

app = FastAPI(title="Backroom API")
# Mount the router under /items to mirror Express-style path grouping
app.include_router(items_router, prefix="/items")

# Example run command:
# uvicorn main:app --reload