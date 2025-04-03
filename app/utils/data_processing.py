import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


def validate_dataframe(df: pd.DataFrame) -> bool:
    """Checks if the DataFrame is valid for processing."""
    return len(df) > 0 and len(df.columns) > 0


def get_numeric_columns(df: pd.DataFrame) -> List[str]:
    """Returns the list of numeric columns."""
    return df.select_dtypes(include=[np.number]).columns.tolist()


def get_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Returns the list of categorical columns."""
    return df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()


def identify_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Identifies and categorizes columns by their data types."""
    return {
        'numeric': get_numeric_columns(df),
        'categorical': get_categorical_columns(df),
        'boolean': df.select_dtypes(include=['bool']).columns.tolist(),
        'datetime': df.select_dtypes(include=['datetime64']).columns.tolist()
    }


def calculate_advanced_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculates advanced statistics on the data."""
    column_types = identify_column_types(df)
    numeric_cols = column_types['numeric']
    
    stats = {
        'basic_stats': df[numeric_cols].describe().to_dict() if numeric_cols else {},
        'correlations': df[numeric_cols].corr().to_dict() if len(numeric_cols) > 1 else {},
        'missing_values': df.isnull().sum().to_dict(),
        'unique_values': {col: df[col].nunique() for col in df.columns},
        'column_types': {col: str(df[col].dtype) for col in df.columns}
    }
    return stats


def filter_dataframe(
    df: pd.DataFrame, column: str, value: Any, operator: str = "equals"
) -> pd.DataFrame:
    """Filters the DataFrame according to specified criteria."""
    if operator == "equals":
        return df[df[column] == value]
    elif operator == "greater_than":
        return df[df[column] > value]
    elif operator == "less_than":
        return df[df[column] < value]
    elif operator == "contains":
        return df[df[column].astype(str).str.contains(str(value), case=False)]
    else:
        raise ValueError(f"Operator {operator} not supported")


def handle_missing_values(
    df: pd.DataFrame,
    strategy: str = "auto",
    columns: Optional[List[str]] = None,
    target_column: Optional[str] = None
) -> pd.DataFrame:
    """Handles missing values while preserving data types and excluding target column."""
    df_copy = df.copy()
    if columns is None:
        columns = [col for col in df.columns if col != target_column]

    column_types = identify_column_types(df_copy)
    original_dtypes = df_copy.dtypes.to_dict()

    for col in columns:
        if df_copy[col].isnull().any():
            if strategy == "auto":
                if col in column_types['numeric']:
                    if df_copy[col].dtype in ['int32', 'int64']:
                        df_copy[col] = df_copy[col].fillna(df_copy[col].median())
                    else:
                        if df_copy[col].skew() > 1 or df_copy[col].skew() < -1:
                            df_copy[col] = df_copy[col].fillna(df_copy[col].median())
                        else:
                            df_copy[col] = df_copy[col].fillna(df_copy[col].mean())
                elif col in column_types['boolean']:
                    df_copy[col] = df_copy[col].fillna(df_copy[col].mode()[0])
                elif col in column_types['datetime']:
                    df_copy[col] = df_copy[col].interpolate(method='time')
                else:
                    if df_copy[col].nunique() / len(df_copy) < 0.05:
                        df_copy[col] = df_copy[col].fillna(df_copy[col].mode()[0])
                    else:
                        df_copy[col] = df_copy[col].fillna('Non spécifié')
            elif strategy in ["mean", "median"] and col in column_types['numeric']:
                value = df_copy[col].median() if strategy == "median" else df_copy[col].mean()
                df_copy[col] = df_copy[col].fillna(value)
            elif strategy == "mode":
                df_copy[col] = df_copy[col].fillna(df_copy[col].mode()[0])

    # Restore original data types
    for col, dtype in original_dtypes.items():
        if col in df_copy.columns:
            try:
                df_copy[col] = df_copy[col].astype(dtype)
            except:
                pass

    return df_copy
    
    return df_copy


def handle_outliers(
    df: pd.DataFrame,
    method: str = "iqr",
    columns: Optional[List[str]] = None,
    target_column: Optional[str] = None
) -> pd.DataFrame:
    """Detects and handles outliers while preserving data types and excluding target column."""
    df_copy = df.copy()
    if columns is None:
        columns = [col for col in get_numeric_columns(df_copy) if col != target_column]

    original_dtypes = df_copy.dtypes.to_dict()

    for col in columns:
        if pd.api.types.is_numeric_dtype(df_copy[col]):
            if method == "iqr":
                Q1 = df_copy[col].quantile(0.25)
                Q3 = df_copy[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df_copy[col] = df_copy[col].clip(lower_bound, upper_bound)
            elif method == "zscore":
                z_scores = (df_copy[col] - df_copy[col].mean()) / df_copy[col].std()
                df_copy[col] = df_copy[col].mask(abs(z_scores) > 3, df_copy[col].median())

    # Restore original data types
    for col, dtype in original_dtypes.items():
        if col in df_copy.columns:
            try:
                df_copy[col] = df_copy[col].astype(dtype)
            except:
                pass

    return df_copy


def remove_duplicates(
    df: pd.DataFrame, subset: Optional[List[str]] = None
) -> pd.DataFrame:
    """Removes duplicate rows from the DataFrame."""
    return df.drop_duplicates(subset=subset, keep="first")


def normalize_data(
    df: pd.DataFrame,
    method: str = "minmax",
    columns: Optional[List[str]] = None,
    target_column: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
    """Normalizes numeric data while preserving integer types and excluding target column."""
    df_copy = df.copy()
    if columns is None:
        columns = [col for col in get_numeric_columns(df_copy) if col != target_column]

    original_dtypes = df_copy.dtypes.to_dict()
    scaling_params = {}

    for col in columns:
        if pd.api.types.is_numeric_dtype(df_copy[col]):
            # Skip boolean columns
            if df_copy[col].dtype == bool:
                continue
                
            if method == "minmax":
                min_val = df_copy[col].min()
                max_val = df_copy[col].max()
                if min_val != max_val:
                    df_copy[col] = (df_copy[col] - min_val) / (max_val - min_val)
                    scaling_params[col] = {"min": float(min_val), "max": float(max_val)}
                    
                    # Preserve integer type if original column was integer
                    if original_dtypes[col] in ['int32', 'int64']:
                        df_copy[col] = (df_copy[col] * 100).round().astype(original_dtypes[col])
            
            elif method == "zscore":
                mean_val = df_copy[col].mean()
                std_val = df_copy[col].std()
                if std_val != 0:
                    df_copy[col] = (df_copy[col] - mean_val) / std_val
                    scaling_params[col] = {"mean": float(mean_val), "std": float(std_val)}

    return df_copy, scaling_params


def transform_data(
    df: pd.DataFrame,
    transformations: List[Dict[str, Any]],
    target_column: Optional[str] = None
) -> pd.DataFrame:
    """Applies a series of transformations while preserving data types and target column."""
    df_copy = df.copy()
    scaling_info = {}

    for transform in transformations:
        operation = transform.get("operation")
        columns = transform.get("columns")

        if operation == "handle_missing":
            strategy = transform.get("strategy", "auto")
            df_copy = handle_missing_values(df_copy, strategy, columns, target_column)
        
        elif operation == "handle_outliers":
            method = transform.get("method", "iqr")
            df_copy = handle_outliers(df_copy, method, columns, target_column)
        
        elif operation == "remove_duplicates":
            subset = transform.get("subset")
            df_copy = remove_duplicates(df_copy, subset)
        
        elif operation == "normalize":
            method = transform.get("method", "minmax")
            df_copy, params = normalize_data(df_copy, method, columns, target_column)
            scaling_info["normalize"] = params
        
        elif operation == "encode_categorical":
            for col in columns or []:
                if col != target_column and col in df_copy.columns:
                    if df_copy[col].dtype == bool:
                        continue  # Skip boolean columns
                    dummies = pd.get_dummies(df_copy[col], prefix=col)
                    df_copy = pd.concat([df_copy, dummies], axis=1)
                    df_copy.drop(col, axis=1, inplace=True)

    return df_copy
