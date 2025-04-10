import xml.etree.ElementTree as ET
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


def validate_xml_structure(xml_string: str) -> Tuple[bool, Optional[ET.Element], str]:
    """Valide la structure XML et retourne un tuple (est_valide, racine_xml, message_erreur)."""
    try:
        # Nettoyer la chaîne XML
        xml_string = xml_string.strip()
        if not xml_string:
            return False, None, "Document XML vide"

        # Parser le XML
        root = ET.fromstring(xml_string)
        return True, root, ""
    except ET.ParseError as e:
        return False, None, f"Erreur de parsing XML: {str(e)}"
    except Exception as e:
        return False, None, f"Erreur inattendue: {str(e)}"


def xml_to_dict(element: ET.Element, parent_path: str = "") -> Dict[str, Any]:
    """Convertit un élément XML en dictionnaire avec gestion des chemins imbriqués et validation des données."""
    try:
        result = {}
        
        # Valider l'élément
        if not isinstance(element, ET.Element):
            logger.error(f"Type d'élément invalide: {type(element)}")
            return {}
        
        # Traiter les attributs avec validation
        for key, value in element.attrib.items():
            if not isinstance(key, str):
                logger.warning(f"Clé d'attribut invalide ignorée: {key}")
                continue
            full_key = f"{parent_path}{key}" if parent_path else key
            result[full_key] = str(value).strip()
        
        # Traiter le texte de l'élément avec validation
        if element.text:
            text = element.text.strip()
            if text and len(element) == 0:
                result[parent_path.rstrip('_')] = text
                return result
        
        # Traiter les éléments enfants avec validation
        for child in element:
            if not isinstance(child.tag, str):
                logger.warning(f"Tag d'élément enfant invalide ignoré")
                continue
                
            child_path = f"{parent_path}{child.tag}_" if parent_path else f"{child.tag}_"
            child_result = xml_to_dict(child, child_path)
            
            if not child_result:
                continue
            
            # Fusionner les résultats avec validation
            for k, v in child_result.items():
                if not isinstance(k, str):
                    logger.warning(f"Clé invalide ignorée: {k}")
                    continue
                    
                if k in result:
                    # Si la clé existe déjà, convertir en liste
                    if not isinstance(result[k], list):
                        result[k] = [result[k]]
                    result[k].append(v)
                else:
                    result[k] = v
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la conversion XML en dictionnaire: {str(e)}")
        return {}



def load_xml_data(xml_file_path: str) -> Optional[pd.DataFrame]:
    """Charge les données XML dans un DataFrame pandas."""
    try:
        logger.info(f"Début du chargement du fichier XML: {xml_file_path}")
        
        # Lire le fichier XML
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        logger.debug(f"XML root tag: {root.tag}")
        children = list(root)
        logger.debug(f"Nombre d'enfants directs: {len(children)}")
        logger.debug(f"Premier tag enfant: {children[0].tag if children else 'Aucun'}")
        
        # Convertir les données XML en liste de dictionnaires
        records = []
        
        # Déterminer si le XML contient une collection d'éléments similaires
        if children and all(child.tag == children[0].tag for child in children):
            # Structure avec éléments répétitifs
            for element in children:
                record = xml_to_dict(element)
                logger.debug(f"Enregistrement converti: {record}")
                if isinstance(record, dict) and record:
                    records.append(record)
                else:
                    logger.warning(f"Enregistrement invalide ignoré: {record}")
        else:
            # Structure unique ou irrégulière
            record = xml_to_dict(root)
            if isinstance(record, dict) and record:
                records.append(record)
            else:
                logger.warning(f"Enregistrement racine invalide: {record}")
        
        logger.debug(f"Records extraits: {records}")
        
        # Validation des records avant création du DataFrame
        if not records or not isinstance(records, list):
            logger.error("Les données extraites sont invalides ou vides.")
            return None
            
        records = [r for r in records if isinstance(r, dict) and r]
        if not records:
            logger.error("Aucun enregistrement valide sous forme de dictionnaire.")
            return None
        
        # Créer le DataFrame
        try:
            df = pd.DataFrame(records)
            logger.debug(f"Colonnes du DataFrame: {df.columns.tolist()}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du DataFrame: {str(e)}")
            return None
        
        # Convertir les types de données
        for col in df.columns:
            # Essayer de convertir en numérique
            try:
                df[col] = pd.to_numeric(df[col], errors='raise')
                continue
            except (ValueError, TypeError):
                pass
            
            # Essayer de convertir en datetime
            try:
                df[col] = pd.to_datetime(df[col], errors='raise')
            except (ValueError, TypeError):
                # Garder comme string si pas numérique ni datetime
                pass
        
        logger.info(f"Traitement terminé: {len(df)} enregistrements chargés")
        return df
    
    except ET.ParseError as e:
        logger.error(f"Erreur de parsing XML: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors du chargement du fichier XML: {str(e)}")
        return None


def save_xml_data(df: pd.DataFrame, xml_file_path: str, root_tag: str = 'data', row_tag: str = 'record') -> bool:
    """Sauvegarde un DataFrame au format XML."""
    try:
        # Créer l'élément racine
        root = ET.Element(root_tag)
        
        # Convertir chaque ligne en élément XML
        for _, row in df.iterrows():
            record = ET.SubElement(root, row_tag)
            
            for col, value in row.items():
                # Ignorer les valeurs None/NaN
                if pd.isna(value):
                    continue
                    
                # Créer un sous-élément pour chaque colonne
                field = ET.SubElement(record, str(col))
                field.text = str(value)
        
        # Créer l'arbre XML et le sauvegarder
        tree = ET.ElementTree(root)
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde en XML: {str(e)}")
        return False


def process_xml_data(xml_string: str, transformations: List[Dict[str, Any]] = None) -> Optional[pd.DataFrame]:
    """Traite les données XML en appliquant des transformations optionnelles."""
    try:
        # Nettoyer et valider la chaîne XML
        if not isinstance(xml_string, str):
            logger.error("L'entrée doit être une chaîne de caractères XML")
            return None

        xml_string = xml_string.strip()
        if not xml_string:
            logger.error("Document XML vide")
            return None

        try:
            # Parser le XML avec une validation plus stricte
            root = ET.fromstring(xml_string)
            if root is None:
                logger.error("Impossible de parser le document XML")
                return None
        except ET.ParseError as e:
            logger.error(f"Erreur de parsing XML: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors du parsing XML: {str(e)}")
            return None

        # Convertir XML en DataFrame
        records = []
        try:
            # Déterminer si le XML contient une collection d'éléments similaires
            children = list(root)
            if not children:
                # Essayer de traiter le root comme un élément unique
                try:
                    record = xml_to_dict(root)
                    if record and isinstance(record, dict):
                        records.append(record)
                    else:
                        logger.error("Impossible de convertir l'élément racine en dictionnaire valide")
                        return None
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion de l'élément racine: {str(e)}")
                    return None
            else:
                # Vérifier si tous les enfants ont le même tag
                first_tag = children[0].tag
                if all(child.tag == first_tag for child in children):
                    # Structure avec éléments répétitifs
                    for element in children:
                        try:
                            record = xml_to_dict(element)
                            if record and isinstance(record, dict):
                                records.append(record)
                            else:
                                logger.warning(f"Élément ignoré: conversion invalide pour {element.tag}")
                        except Exception as e:
                            logger.warning(f"Erreur lors de la conversion de l'élément {element.tag}: {str(e)}")
                            continue
                else:
                    # Structure unique ou irrégulière
                    try:
                        record = xml_to_dict(root)
                        if record and isinstance(record, dict):
                            records.append(record)
                        else:
                            logger.error("Impossible de convertir la structure irrégulière en dictionnaire valide")
                            return None
                    except Exception as e:
                        logger.error(f"Erreur lors de la conversion de la structure irrégulière: {str(e)}")
                        return None

            if not records:
                logger.error("Aucun enregistrement valide trouvé dans le document XML")
                return None

            # Créer le DataFrame
            df = pd.DataFrame(records)
            if df.empty:
                logger.error("Le DataFrame généré est vide")
                return None

            # Convertir les types de données
            for col in df.columns:
                # Essayer de convertir en numérique
                try:
                    df[col] = pd.to_numeric(df[col], errors='raise')
                    continue
                except (ValueError, TypeError):
                    pass

                # Essayer de convertir en datetime
                try:
                    df[col] = pd.to_datetime(df[col], errors='raise')
                except (ValueError, TypeError):
                    # Garder comme string si pas numérique ni datetime
                    pass

            # Appliquer les transformations si spécifiées
            if transformations:
                df = transform_data(df, transformations)
                if df is None or df.empty:
                    logger.error("Échec des transformations sur les données")
                    return None

            logger.info(f"Traitement réussi: {len(df)} enregistrements chargés")
            return df

        except ValueError as ve:
            logger.error(f"Erreur de conversion des données: {str(ve)}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors du traitement des données: {str(e)}")
            return None

    except Exception as e:
        logger.error(f"Erreur lors du traitement des données XML: {str(e)}")
        return None


def xml_to_csv(xml_file_path: str, csv_file_path: str) -> bool:
    """Convertit un fichier XML en CSV."""
    try:
        # Charger les données XML en DataFrame
        df = load_xml_data(xml_file_path)
        if df is None:
            logger.error(f"Échec du chargement du fichier XML: {xml_file_path}")
            return False
            
        # Sauvegarder en CSV
        try:
            df.to_csv(csv_file_path, index=False, encoding='utf-8')
            logger.info(f"Fichier CSV créé avec succès: {csv_file_path}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde en CSV: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors de la conversion XML vers CSV: {str(e)}")
        return False