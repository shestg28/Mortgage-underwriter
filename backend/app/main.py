from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.customers import router as customers_router
from app.routers.documents import router as documents_router
from app.routers.applications import router as applications_router
from app.routers.fraud_flags import router as fraud_flags_router
from app.routers.health import router as health_router
from app.db import init_db

app = FastAPI(
    title="Speckit Mortgage Underwriting API",
    version="0.1.0",
    description="Backend API for mortgage underwriting, verification, and fraud detection.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(documents_router)
app.include_router(applications_router)
app.include_router(fraud_flags_router)


@app.on_event("startup")
def on_startup():
    init_db()
