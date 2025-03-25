from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import data_routes

app = FastAPI(
    title="API de Traitement de Données",
    description="API REST pour le traitement et l'analyse de données",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes
app.include_router(data_routes.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)