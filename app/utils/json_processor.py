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
        current_object = ""
        
        with open(json_file_path, 'r', encoding='utf-8') as file:
            # Lire le fichier ligne par ligne pour éviter les problèmes de mémoire
            lines = []
            for line in file:
                line = line.strip()
                if line:  # Ignorer les lignes vides
                    lines.append(line)
            
            if not lines:
                logger.error("Fichier JSON vide")
                return None
            
            # Traiter chaque ligne individuellement
            for line_number, line in enumerate(lines, 1):
                # Nettoyer la ligne
                cleaned_line = ''.join(c for c in line if c.isprintable() or c.isspace()).strip()
                if not cleaned_line:
                    continue
                
                # Supprimer les caractères parasites
                while any(cleaned_line.endswith(c) for c in [',', ']', '}', ' ']):
                    cleaned_line = cleaned_line[:-1].strip()
                
                # Détecter si la ligne fait partie d'un objet JSON incomplet
                if current_object:
                    # Ajouter la ligne au current_object
                    current_object += " " + cleaned_line
                    # Vérifier si l'objet est complet
                    try:
                        data = json.loads(current_object)
                        if isinstance(data, dict):
                            valid_records.append(flatten_json(data))
                        current_object = ""
                        continue
                    except json.JSONDecodeError:
                        # L'objet n'est pas encore complet, continuer à la prochaine ligne
                        continue
                
                # Essayer de parser la ligne comme JSON
                is_valid, data, error_message = validate_json_line(cleaned_line)
                
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
                    # Vérifier si c'est le début d'un nouvel objet
                    if cleaned_line.startswith('{') and not cleaned_line.endswith('}'):
                        current_object = cleaned_line
                        continue
                    
                    # Essayer de corriger le format JSON
                    try:
                        # Vérifier si la ligne fait partie d'un tableau JSON
                        if cleaned_line.startswith('[') or cleaned_line.endswith(']'):
                            cleaned_line = cleaned_line.strip('[]').strip()
                        
                        # Ajouter des accolades si nécessaire
                        if not cleaned_line.startswith('{'):
                            cleaned_line = '{' + cleaned_line
                        if not cleaned_line.endswith('}'):
                            cleaned_line = cleaned_line + '}'
                        
                        # Réessayer le parsing
                        data = json.loads(cleaned_line)
                        if isinstance(data, dict):
                            valid_records.append(flatten_json(data))
                        else:
                            logger.warning(f"Ligne {line_number}: Format non supporté après correction")
                    except json.JSONDecodeError:
                        logger.error(f"Ligne {line_number}: {error_message}")
                        invalid_lines.append((line_number, cleaned_line, error_message))
        
        # Créer le DataFrame si nous avons des enregistrements valides
        if valid_records:
            logger.info(f"Traitement terminé: {len(valid_records)} enregistrements valides trouvés")
            if invalid_lines:
                logger.warning(f"{len(invalid_lines)} lignes invalides trouvées:")
                for line_num, line, error in invalid_lines:
                    logger.warning(f"Ligne {line_num}: {error}\nContenu: {line[:100]}...")
            
            # Créer le DataFrame et gérer les types de données
            df = pd.DataFrame(valid_records)
            
            # Convertir les colonnes en types appropriés
            for col in df.columns:
                # Essayer de convertir en numérique si possible
                try:
                    df[col] = pd.to_numeric(df[col], errors='raise')
                except (ValueError, TypeError):
                    # Essayer de convertir en datetime si possible
                    try:
                        df[col] = pd.to_datetime(df[col], errors='raise')
                    except (ValueError, TypeError):
                        # Garder comme string si pas numérique ni datetime
                        pass
            
            return df
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