"""FastAPI main entry point for the cultivation life simulator."""
from .logging_config import setup_logging

# Initialize logging before anything else
setup_logging(log_dir="logs", level="INFO")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .router import router

app = FastAPI(
    title="觅长生 - 修仙人生重开模拟器",
    description="A cultivation-themed life restart simulator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "觅长生 - 修仙人生重开模拟器 API", "version": "1.0.0"}
