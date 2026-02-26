from fastapi import FastAPI
from app.routes import health
from app.core.config import APP_NAME
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)

@app.get("/")
def root():
    return {"message": "Server is running"}