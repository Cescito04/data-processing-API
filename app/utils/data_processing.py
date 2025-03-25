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

def handle_missing_values(df: pd.DataFrame, strategy: str = 'mean', columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Traite les valeurs manquantes dans le DataFrame."""
    df_copy = df.copy()
    if columns is None:
        columns = df.columns
    
    for col in columns:
        if df_copy[col].isnull().any():
            if strategy == 'mean' and pd.api.types.is_numeric_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].fillna(df_copy[col].mean())
            elif strategy == 'median' and pd.api.types.is_numeric_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].fillna(df_copy[col].median())
            elif strategy == 'mode':
                df_copy[col] = df_copy[col].fillna(df_copy[col].mode()[0])
            elif strategy == 'drop':
                df_copy = df_copy.dropna(subset=[col])
    return df_copy

def handle_outliers(df: pd.DataFrame, method: str = 'iqr', columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Détecte et traite les valeurs aberrantes."""
    df_copy = df.copy()
    if columns is None:
        columns = get_numeric_columns(df_copy)
    
    for col in columns:
        if pd.api.types.is_numeric_dtype(df_copy[col]):
            if method == 'iqr':
                Q1 = df_copy[col].quantile(0.25)
                Q3 = df_copy[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df_copy[col] = df_copy[col].clip(lower_bound, upper_bound)
            elif method == 'zscore':
                z_scores = (df_copy[col] - df_copy[col].mean()) / df_copy[col].std()
                df_copy[col] = df_copy[col].mask(abs(z_scores) > 3, df_copy[col].mean())
    return df_copy

def remove_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
    """Supprime les lignes dupliquées du DataFrame."""
    return df.drop_duplicates(subset=subset, keep='first')

def normalize_data(df: pd.DataFrame, method: str = 'minmax', columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Normalise les données numériques du DataFrame."""
    df_copy = df.copy()
    if columns is None:
        columns = get_numeric_columns(df_copy)
    
    for col in columns:
        if pd.api.types.is_numeric_dtype(df_copy[col]):
            if method == 'minmax':
                min_val = df_copy[col].min()
                max_val = df_copy[col].max()
                df_copy[col] = (df_copy[col] - min_val) / (max_val - min_val)
            elif method == 'zscore':
                df_copy[col] = (df_copy[col] - df_copy[col].mean()) / df_copy[col].std()
    return df_copy

def transform_data(df: pd.DataFrame, transformations: List[Dict[str, Any]]) -> pd.DataFrame:
    """Applique une série de transformations au DataFrame."""
    df_copy = df.copy()
    for transform in transformations:
        operation = transform.get('operation')
        
        if operation == 'handle_missing':
            strategy = transform.get('strategy', 'mean')
            columns = transform.get('columns')
            df_copy = handle_missing_values(df_copy, strategy, columns)
        elif operation == 'handle_outliers':
            method = transform.get('method', 'iqr')
            columns = transform.get('columns')
            df_copy = handle_outliers(df_copy, method, columns)
        elif operation == 'remove_duplicates':
            subset = transform.get('subset')
            df_copy = remove_duplicates(df_copy, subset)
        elif operation == 'normalize':
            method = transform.get('method', 'minmax')
            columns = transform.get('columns')
            df_copy = normalize_data(df_copy, method, columns)
        elif operation == 'one_hot_encode':
            column = transform.get('column')
            dummies = pd.get_dummies(df_copy[column], prefix=column)
            df_copy = pd.concat([df_copy, dummies], axis=1)
            df_copy.drop(column, axis=1, inplace=True)
            
    return df_copy