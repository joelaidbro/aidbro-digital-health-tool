from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.audit import router as audit_router

app = FastAPI(
    title="Aidbro Digital Health API",
    description="AI-powered digital presence analyzer for local businesses",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "Aidbro Digital Health API is running", "version": "1.0.0"}