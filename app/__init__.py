from fastapi import FastAPI
from .services.data_service import DataService

# Initialisation du service de données
data_service = DataService("data/database.sqlite")
