import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Any
from datetime import datetime
import pandas as pd
import numpy as np


def validate_xml_structure(xml_string: str) -> Tuple[bool, ET.Element, str]:
    """Validates XML structure and returns a tuple (is_valid, root_element, error)."""
    
    # Vérification préliminaire du format XML
    if not xml_string or not xml_string.strip():
        return False, None, "Le fichier XML est vide"
    
    # Vérifier la présence de la balise d'ouverture XML
    if not xml_string.strip().startswith('<'):
        return False, None, "Format XML invalide : le fichier doit commencer par une balise d'ouverture '<'"
    
    try:
        root = ET.fromstring(xml_string)
        
        # Vérification de l'élément racine
        if not root.tag:
            return False, None, "Le document XML n'a pas d'élément racine"
            
        # Vérifier si l'élément racine a des enfants
        if len(root) == 0:
            return False, None, "Le document XML est vide (pas d'éléments enfants)"
            
        return True, root, ""
        
    except ET.ParseError as e:
        # Amélioration des messages d'erreur
        error_msg = str(e)
        if 'no element found' in error_msg.lower():
            return False, None, "Format XML invalide : aucun élément XML trouvé dans le fichier"
        elif 'not well-formed' in error_msg.lower():
            return False, None, "Format XML invalide : le document n'est pas bien formé (vérifiez les balises ouvrantes/fermantes)"
        else:
            return False, None, f"Erreur de structure XML : {error_msg}"
    except Exception as e:
        return False, None, f"Erreur inattendue lors de l'analyse XML : {str(e)}"


def detect_xml_data_types(element: ET.Element, path: str = "") -> Dict[str, str]:
    """Automatically detects data types for XML elements."""
    type_mapping = {}
    current_path = f"{path}/{element.tag}" if path else element.tag
    
    # Check element text
    if element.text and element.text.strip():
        text_value = element.text.strip()
        
        # Try to detect datetime
        try:
            pd.to_datetime(text_value)
            type_mapping[current_path] = "datetime"
        except (ValueError, TypeError):
            # Try to detect numeric types
            try:
                float_val = float(text_value)
                if float_val.is_integer():
                    type_mapping[current_path] = "integer"
                else:
                    type_mapping[current_path] = "float"
            except ValueError:
                # If not numeric, check if boolean
                if text_value.lower() in ["true", "false", "1", "0"]:
                    type_mapping[current_path] = "boolean"
                else:
                    type_mapping[current_path] = "text"
    
    # Process attributes
    for attr_name, attr_value in element.attrib.items():
        attr_path = f"{current_path}/@{attr_name}"
        try:
            float_val = float(attr_value)
            if float_val.is_integer():
                type_mapping[attr_path] = "integer"
            else:
                type_mapping[attr_path] = "float"
        except ValueError:
            try:
                pd.to_datetime(attr_value)
                type_mapping[attr_path] = "datetime"
            except (ValueError, TypeError):
                if attr_value.lower() in ["true", "false", "1", "0"]:
                    type_mapping[attr_path] = "boolean"
                else:
                    type_mapping[attr_path] = "text"
    
    # Recursively process child elements
    for child in element:
        type_mapping.update(detect_xml_data_types(child, current_path))
    
    return type_mapping


def validate_xml_data(xml_string: str) -> Tuple[bool, List[str]]:
    """Validates XML data and returns a tuple (is_valid, error_list)."""
    errors = []
    
    # First validate XML structure
    is_valid, root, structure_error = validate_xml_structure(xml_string)
    if not is_valid:
        return False, [structure_error]
    
    # No need to parse XML again since we already have the root element
    
    # Detect and validate data types
    data_types = detect_xml_data_types(root)
    
    for path, dtype in data_types.items():
        element = root.find(path.split('@')[0]) if '@' not in path else root.find(path.split('@')[0])
        
        if element is None:
            continue
        
        value = element.text if '@' not in path else element.attrib[path.split('@')[1]]
        if not value or not value.strip():
            continue
            
        value = value.strip()
        
        if dtype in ["integer", "float"]:
            try:
                float(value)
            except ValueError:
                errors.append(f"Element at path '{path}' contains non-numeric value: {value}")
        
        elif dtype == "datetime":
            try:
                pd.to_datetime(value)
            except (ValueError, TypeError):
                errors.append(f"Element at path '{path}' contains invalid date: {value}")
        
        elif dtype == "boolean":
            if value.lower() not in ["true", "false", "1", "0"]:
                errors.append(f"Element at path '{path}' contains invalid boolean value: {value}")
    
    return len(errors) == 0, errors


def generate_xml_profile(xml_string: str) -> Dict[str, Any]:
    """Generates a detailed profile of the XML data."""
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError:
        return {"error": "Invalid XML structure"}
    
    profile = {
        "root_element": root.tag,
        "total_elements": len(root.findall(".//*")) + 1,  # +1 for root
        "total_attributes": sum(len(elem.attrib) for elem in root.findall(".//*")) + len(root.attrib),
        "max_depth": 0,
        "data_types": detect_xml_data_types(root),
        "element_counts": {},
        "attribute_stats": {}
    }
    
    # Calculate maximum depth and element counts
    def process_element(element, depth=0):
        nonlocal profile
        profile["max_depth"] = max(profile["max_depth"], depth)
        
        # Count elements
        if element.tag in profile["element_counts"]:
            profile["element_counts"][element.tag] += 1
        else:
            profile["element_counts"][element.tag] = 1
        
        # Process attributes
        for attr_name in element.attrib:
            if attr_name not in profile["attribute_stats"]:
                profile["attribute_stats"][attr_name] = {
                    "count": 0,
                    "unique_values": set()
                }
            profile["attribute_stats"][attr_name]["count"] += 1
            profile["attribute_stats"][attr_name]["unique_values"].add(element.attrib[attr_name])
        
        for child in element:
            process_element(child, depth + 1)
    
    process_element(root)
    
    # Convert sets to lists for JSON serialization
    for attr in profile["attribute_stats"]:
        profile["attribute_stats"][attr]["unique_values"] = \
            list(profile["attribute_stats"][attr]["unique_values"])
    
    return profile