import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

def validate_dataframe(df: pd.DataFrame) -> bool:
    """Vérifie si le DataFrame est valide pour le traitement."""
    return len(df) > 0 and len(df.columns) > 0

def get_numeric_columns(df: pd.DataFrame) -> List[str]:
    """Retourne la liste des colonnes numériques."""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def get_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Retourne la liste des colonnes catégorielles."""
    return df.select_dtypes(include=['object', 'category']).columns.tolist()

def calculate_advanced_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcule des statistiques avancées sur les données."""
    numeric_cols = get_numeric_columns(df)
    stats = {
        'basic_stats': df[numeric_cols].describe().to_dict(),
        'correlations': df[numeric_cols].corr().to_dict() if len(numeric_cols) > 1 else {},
        'missing_values': df.isnull().sum().to_dict(),
        'unique_values': {col: df[col].nunique() for col in df.columns}
    }
    return stats

def filter_dataframe(df: pd.DataFrame, column: str, value: Any, operator: str = 'equals') -> pd.DataFrame:
    """Filtre le DataFrame selon les critères spécifiés."""
    if operator == 'equals':
        return df[df[column] == value]
    elif operator == 'greater_than':
        return df[df[column] > value]
    elif operator == 'less_than':
        return df[df[column] < value]
    elif operator == 'contains':
        return df[df[column].astype(str).str.contains(str(value), case=False)]
    else:
        raise ValueError(f"Opérateur {operator} non supporté")

def transform_data(df: pd.DataFrame, transformations: List[Dict[str, Any]]) -> pd.DataFrame:
    """Applique une série de transformations au DataFrame."""
    df_copy = df.copy()
    for transform in transformations:
        operation = transform.get('operation')
        column = transform.get('column')
        
        if operation == 'normalize':
            df_copy[column] = (df_copy[column] - df_copy[column].mean()) / df_copy[column].std()
        elif operation == 'fill_na':
            value = transform.get('value')
            df_copy[column] = df_copy[column].fillna(value)
        elif operation == 'one_hot_encode':
            dummies = pd.get_dummies(df_copy[column], prefix=column)
            df_copy = pd.concat([df_copy, dummies], axis=1)
            df_copy.drop(column, axis=1, inplace=True)
            
    return df_copy