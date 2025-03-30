from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Response
from ..services.data_service import DataService
from typing import List, Optional
import pandas as pd
import io
from ..utils.data_processing import (
    handle_missing_values,
    handle_outliers,
    remove_duplicates,
    normalize_data
)

router = APIRouter()
data_service = DataService("data/database.sqlite")

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Vérifier le type de fichier
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Le fichier doit être au format CSV"
            )
        
        # Lire le contenu du fichier
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # Sauvegarder les données
        if data_service.save_dataframe(df):
            return {"message": "Fichier CSV chargé avec succès", "rows": len(df), "columns": df.columns.tolist()}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde des données")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process/")
async def process_data(
    handle_missing: str = Query("mean", description="Stratégie de gestion des valeurs manquantes (mean, median, mode, drop)"),
    handle_outliers_method: str = Query("iqr", description="Méthode de gestion des valeurs aberrantes (iqr, zscore)"),
    normalize_method: str = Query("minmax", description="Méthode de normalisation (minmax, zscore)"),
    columns: Optional[List[str]] = Query(None, description="Colonnes à traiter (toutes si non spécifié)")
):
    try:
        # Récupérer les données
        df = data_service.get_dataframe()
        if df is None:
            raise HTTPException(status_code=404, detail="Aucune donnée trouvée")
        
        # Traiter les données
        df = handle_missing_values(df, strategy=handle_missing, columns=columns)
        df = handle_outliers(df, method=handle_outliers_method, columns=columns)
        df = remove_duplicates(df)
        df = normalize_data(df, method=normalize_method, columns=columns)
        
        # Sauvegarder les données traitées
        if data_service.save_dataframe(df):
            return {"message": "Données traitées avec succès", "rows": len(df), "columns": df.columns.tolist()}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde des données traitées")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/")
async def export_data():
    try:
        df = data_service.get_dataframe()
        if df is None:
            raise HTTPException(status_code=404, detail="Aucune donnée trouvée")
        
        # Convertir en CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        response = Response(content=output.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=data_processed.csv"
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/")
async def get_statistics():
    try:
        stats = data_service.get_statistics()
        if stats is None:
            raise HTTPException(status_code=404, detail="Aucune donnée trouvée")
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))