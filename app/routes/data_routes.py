from fastapi import APIRouter, UploadFile, File, HTTPException, Path
from fastapi.responses import Response
from typing import List, Dict, Any
import pandas as pd
import sqlite3
from ..models.data_models import FilterRequest, StatisticsResponse, ErrorResponse, SuccessResponse
from .. import data_service

router = APIRouter()

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Vérifier l'extension du fichier
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        elif file.filename.endswith('.json'):
            df = pd.read_json(file.file)
        else:
            raise HTTPException(status_code=400, detail="Format de fichier non supporté")
        
        # Sauvegarder les données dans SQLite
        with sqlite3.connect("data/database.sqlite") as conn:
            df.to_sql('data_table', conn, if_exists='replace', index=False)
        
        return {"message": "Fichier uploadé avec succès", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/", response_model=StatisticsResponse)
async def get_statistics():
    try:
        stats = data_service.get_statistics()
        if stats is None:
            raise HTTPException(status_code=404, detail="No data available")
        return StatisticsResponse(
            count=stats['basic_stats']['count'],
            columns=list(stats['basic_stats'].keys()),
            numeric_stats=stats['basic_stats'],
            missing_values=stats['missing_values']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/filter/")
async def filter_data(filter_request: FilterRequest):
    try:
        result = data_service.filter_data(
            column=filter_request.column,
            value=filter_request.value,
            operator=filter_request.operator
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Données non trouvées")
        return result.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transform/")
async def transform_data(transformations: List[Dict[str, Any]]):
    try:
        result = data_service.apply_transformations(transformations)
        if result is None:
            raise HTTPException(status_code=400, detail="Erreur lors de la transformation")
        return SuccessResponse(
            message="Transformation réussie",
            data=result.to_dict(orient='records')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{format}")
async def export_data(format: str = Path(..., regex="^(csv|json)$")):
    try:
        df = data_service.get_dataframe()
        if df is None:
            raise HTTPException(status_code=404, detail="No data available")
        
        if format == "csv":
            return Response(
                df.to_csv(index=False),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=data.csv"}
            )
        else:
            return Response(
                df.to_json(orient='records'),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=data.json"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))