from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Response
from ..services.data_service import DataService
from typing import List, Optional
import pandas as pd
import io
from ..utils.data_processing import (
    handle_missing_values,
    handle_outliers,
    remove_duplicates,
    normalize_data,
)
from ..utils.csv_validator import validate_csv_data, generate_data_profile
from ..utils.csv_processor import CSVProcessor
from ..utils.xml_processor import xml_to_csv
import os

router = APIRouter()
data_service = DataService("data/database.sqlite")


@router.post("/transform-xml-to-csv/{file_id}")
async def transform_to_csv(file_id: int):
    try:
        # Récupérer le fichier XML
        file_info = data_service.get_file(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="Fichier non trouvé")
            
        if file_info['file_type'].lower() != 'xml':
            raise HTTPException(status_code=400, detail="Le fichier doit être au format XML")
            
        # Créer le chemin pour le fichier CSV
        xml_path = file_info['file_path']
        csv_path = os.path.splitext(xml_path)[0] + '.csv'
        
        # Convertir XML en CSV
        if xml_to_csv(xml_path, csv_path):
            # Mettre à jour les informations du fichier dans la base de données
            data_service.update_file_type(file_id, 'csv', csv_path)
            return {"message": "Fichier converti avec succès en CSV"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la conversion du fichier")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Check file type
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="File must be in CSV format")

        # Read file content
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))

        # Validate data
        is_valid, errors = validate_csv_data(df)
        if not is_valid:
            raise HTTPException(status_code=400, detail={"errors": errors})

        # Generate data profile
        data_profile = generate_data_profile(df)

        # Save data
        if data_service.save_dataframe(df):
            return {
                "message": "CSV file uploaded successfully",
                "rows": len(df),
                "columns": df.columns.tolist(),
                "profile": data_profile,
            }
        else:
            raise HTTPException(status_code=500, detail="Error saving data")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/")
async def process_data(
    auto_clean: bool = Query(True, description="Enable automatic data cleaning"),
    handle_missing: str = Query(
        "mean",
        description="Missing values handling strategy (mean, median, mode, drop)",
    ),
    handle_outliers_method: str = Query(
        "iqr", description="Outliers handling method (iqr, zscore)"
    ),
    normalize_method: str = Query(
        "minmax", description="Normalization method (minmax, zscore)"
    ),
    columns: Optional[List[str]] = Query(
        None, description="Columns to process (all if not specified)"
    ),
):
    try:
        # Retrieve data
        df = data_service.get_dataframe()
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")

        # Initialize CSV processor
        processor = CSVProcessor(df)

        if auto_clean:
            # Automatic processing
            df = processor.auto_clean()
            summary = processor.get_processing_summary()
            quality_scores = processor.get_data_quality_score()
        else:
            # Manual processing
            df = handle_missing_values(df, strategy=handle_missing, columns=columns)
            df = handle_outliers(df, method=handle_outliers_method, columns=columns)
            df = remove_duplicates(df)
            df = normalize_data(df, method=normalize_method, columns=columns)
            summary = {"message": "Manual processing completed"}
            quality_scores = None

        # Save processed data
        if data_service.save_dataframe(df):
            return {
                "message": "Data processed successfully",
                "rows": len(df),
                "columns": df.columns.tolist(),
                "processing_summary": summary,
                "quality_scores": quality_scores,
            }
        else:
            raise HTTPException(status_code=500, detail="Error saving processed data")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/")
async def export_data():
    try:
        df = data_service.get_dataframe()
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")

        # Convert to CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        response = Response(content=output.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = (
            "attachment; filename=data_processed.csv"
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/")
async def get_statistics():
    try:
        stats = data_service.get_statistics()
        if stats is None:
            raise HTTPException(status_code=404, detail="No data found")
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
