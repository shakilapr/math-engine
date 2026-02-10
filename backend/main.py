"""
MathEngine Backend - FastAPI Application
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from api.routes import router as api_router
from api.routes_self_edit import router as self_edit_router
from api.ws import router as ws_router

load_dotenv()

app = FastAPI(
    title="MathEngine",
    description="The math tutor you never asked for",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure output dirs exist
os.makedirs("outputs/plots", exist_ok=True)
os.makedirs("outputs/pdfs", exist_ok=True)

app.mount("/static", StaticFiles(directory="outputs"), name="static")

app.include_router(api_router, prefix="/api")
app.include_router(self_edit_router, prefix="/api")
app.include_router(ws_router, prefix="/ws")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MathEngine"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
