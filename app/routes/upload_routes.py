from fastapi import APIRouter, UploadFile, HTTPException
from tempfile import NamedTemporaryFile
import shutil
from ..utils.json_processor import load_json_data

router = APIRouter()

@router.post("/upload/json/")
async def upload_json(file: UploadFile):
    """Endpoint pour uploader et traiter un fichier JSON."""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format JSON")

    try:
        # Créer un fichier temporaire pour stocker le contenu
        with NamedTemporaryFile(delete=False) as temp_file:
            # Copier le contenu du fichier uploadé dans le fichier temporaire
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        # Charger et traiter le JSON
        df = load_json_data(temp_path)

        if df is not None:
            # Convertir le DataFrame en dictionnaire pour la réponse JSON
            result = df.to_dict(orient='records')
            return {"message": "Fichier chargé avec succès", "data": result}
        else:
            raise HTTPException(
                status_code=400,
                detail="Impossible de charger le fichier JSON. Vérifiez le format du fichier."
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement du fichier: {str(e)}"
        )
    finally:
        # S'assurer que le fichier est fermé
        file.file.close()