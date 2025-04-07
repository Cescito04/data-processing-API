from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import data_routes, upload_routes

app = FastAPI(
    title="Data Processing API",
    description="REST API for data processing and data analysis",
    version="1.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root path redirect
@app.get("/")
async def root():
    return {"message": "Welcome to Data Processing API", "docs": "/docs"}


# Include routes
app.include_router(data_routes.router, prefix="/api/v1")
app.include_router(upload_routes.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
