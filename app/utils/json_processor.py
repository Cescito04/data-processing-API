import json
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from .data_processing import (
    validate_dataframe,
    calculate_advanced_stats,
    filter_dataframe,
    transform_data,
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_json_line(line: str) -> Tuple[bool, Optional[dict], str]:
    """Valide une ligne de JSON et retourne un tuple (est_valide, données_parsées, message_erreur)."""
    try:
        line = line.strip()
        if not line:
            return False, None, "Ligne vide"
            
        # Nettoyer la ligne
        cleaned_line = ''.join(c for c in line if c.isprintable() or c.isspace()).strip()
        if not cleaned_line:
            return False, None, "Ligne ne contient que des caractères non imprimables"
            
        # Supprimer les caractères parasites
        while any(cleaned_line.endswith(c) for c in [',', ']', '}', ' ']):
            cleaned_line = cleaned_line[:-1].strip()
        
        # Essayer de parser le JSON
        try:
            data = json.loads(cleaned_line)
            return True, data, ""
        except json.JSONDecodeError:
            # Essayer d'ajouter les accolades manquantes
            if not cleaned_line.startswith('{'):
                cleaned_line = '{' + cleaned_line
            if not cleaned_line.endswith('}'):
                cleaned_line = cleaned_line + '}'
            
            try:
                data = json.loads(cleaned_line)
                return True, data, ""
            except json.JSONDecodeError as e:
                return False, None, f"Erreur de parsing JSON: {str(e)}"
    except Exception as e:
        return False, None, f"Erreur inattendue: {str(e)}"

def load_json_data(json_file_path: str) -> Optional[pd.DataFrame]:
    """Charge les données JSON dans un DataFrame pandas avec gestion des fichiers semi-structurés.
    Transforme automatiquement les données en tableau JSON valide lors de l'upload."""
    try:
        logger.info(f"Début du chargement du fichier JSON: {json_file_path}")
        valid_records = []
        invalid_lines = []
        
        with open(json_file_path, 'r') as file:
            content = file.read()
            logger.info("Fichier lu avec succès")
            
            # Nettoyer et normaliser le contenu
            content = content.strip()
            content = ''.join(char for char in content if char.isprintable() or char.isspace()).strip()
            
            # Supprimer les caractères parasites et les virgules trailing
            while content and content[-1] in [',', ']', '}', ' ', '\n', '\r']:
                content = content[:-1].strip()
            
            # Normaliser les séparateurs d'objets
            content = content.replace('}\n{', '},{').replace('}{', '},{')
            content = content.replace('}\r\n{', '},{').replace('}\r{', '},{')
            
            # Assurer que le contenu est un tableau JSON valide
            if not content:
                logger.error("Fichier JSON vide")
                return None
            
            # Détecter et nettoyer le format du contenu JSON
            if content:
                # Détecter et transformer le format
                if content.startswith('[') and content.endswith(']'):
                    logger.info("Format détecté: Tableau JSON")
                elif content.startswith('{') and content.endswith('}'):
                    logger.info("Format détecté: Objet JSON unique")
                    content = '[' + content + ']'
                else:
                    # Essayer de détecter une série d'objets JSON
                    if content[0] == '{' or content.strip().startswith('{'):
                        logger.info("Format détecté: Série d'objets JSON")
                        # Nettoyer et transformer en tableau JSON valide
                        content = '[' + content + ']'
                    else:
                        # Essayer de traiter comme des lignes JSON séparées
                        logger.info("Format détecté: Lignes JSON séparées")
                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                        content = '[' + ','.join(lines) + ']'
                
                logger.info("Transformation en tableau JSON effectuée")
            
            try:
                # Essayer d'abord de charger le fichier entier comme un JSON unique
                logger.info("Tentative de chargement du fichier comme JSON unique")
                data = json.loads(content)
                if isinstance(data, list):
                    logger.info("Format détecté: Liste JSON")
                    for item in data:
                        if isinstance(item, dict):
                            valid_records.append(flatten_json(item))
                        else:
                            logger.warning(f"Élément ignoré: {item} (type non supporté)")
                elif isinstance(data, dict):
                    logger.info("Format détecté: Objet JSON unique")
                    valid_records.append(flatten_json(data))
            except json.JSONDecodeError as e:
                logger.info(f"Le fichier n'est pas un JSON unique, passage au traitement ligne par ligne. Erreur: {str(e)}")
                # Si le fichier n'est pas un JSON unique, traiter ligne par ligne
                line_number = 0
                for line in content.split('\n'):
                    line_number += 1
                    is_valid, data, error_message = validate_json_line(line)
                    
                    if is_valid:
                        if isinstance(data, dict):
                            valid_records.append(flatten_json(data))
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    valid_records.append(flatten_json(item))
                                else:
                                    logger.warning(f"Ligne {line_number}: Élément ignoré (type non supporté)")
                    else:
                        if line.strip():  # Ne pas logger les lignes vides
                            logger.error(f"Ligne {line_number}: {error_message}")
                            invalid_lines.append((line_number, line.strip(), error_message))
        
        # Si nous avons des enregistrements valides, créer un DataFrame
        if valid_records:
            logger.info(f"Traitement terminé: {len(valid_records)} enregistrements valides trouvés")
            if invalid_lines:
                logger.warning(f"{len(invalid_lines)} lignes invalides trouvées:")
                for line_num, line, error in invalid_lines:
                    logger.warning(f"Ligne {line_num}: {error}\nContenu: {line[:100]}...")
            return pd.DataFrame(valid_records)
        else:
            logger.error("Aucun enregistrement valide trouvé dans le fichier")
            return None
    except Exception as e:
        logger.error(f"Erreur lors du chargement du fichier JSON: {str(e)}")
        return None


def save_json_data(df: pd.DataFrame, json_file_path: str, orient: str = 'records') -> bool:
    """Sauvegarde un DataFrame au format JSON avec le format spécifié."""
    try:
        # Convertir le DataFrame en JSON avec le format demandé
        json_data = df.to_json(orient=orient, force_ascii=False)
        parsed_data = json.loads(json_data)
        
        # Écrire dans le fichier avec une indentation propre
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde en JSON: {str(e)}")
        return False


def validate_json_structure(json_data: str) -> bool:
    """Valide la structure des données JSON."""
    try:
        # Tente de parser les données JSON
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        # Vérifie si les données sont une liste d'objets ou un objet
        if not (isinstance(data, list) or isinstance(data, dict)):
            return False

        # Si c'est une liste, vérifie que tous les éléments sont des objets
        if isinstance(data, list):
            return all(isinstance(item, dict) for item in data)

        return True
    except json.JSONDecodeError:
        return False
    except Exception:
        return False


def flatten_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Aplatit un objet JSON imbriqué."""
    out = {}

    def flatten(x: Any, name: str = ''):
        if isinstance(x, dict):
            for a in x:
                flatten(x[a], name + a + '_')
        elif isinstance(x, list):
            for i, a in enumerate(x):
                flatten(a, name + str(i) + '_')
        else:
            out[name[:-1]] = x

    flatten(data)
    return out


def process_json_data(json_data: str, transformations: List[Dict[str, Any]] = None) -> Optional[pd.DataFrame]:
    """Traite les données JSON en appliquant des transformations optionnelles."""
    try:
        # Valide d'abord la structure JSON
        if not validate_json_structure(json_data):
            return None

        # Convertit les données JSON en DataFrame
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            # Pour les objets JSON, aplatir la structure
            flattened_data = flatten_json(data)
            df = pd.DataFrame([flattened_data])

        # Applique les transformations si spécifiées
        if transformations and not df.empty:
            df = transform_data(df, transformations)

        return df
    except Exception as e:
        print(f"Erreur lors du traitement des données JSON: {str(e)}")
        return None