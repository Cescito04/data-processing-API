import pandas as pd
from typing import Dict, List, Tuple, Any
import numpy as np


def detect_data_types(df: pd.DataFrame) -> Dict[str, str]:
    """Automatically detects data types for each column."""
    type_mapping = {}

    for column in df.columns:
        # Check if column contains dates
        try:
            pd.to_datetime(df[column], errors="raise")
            type_mapping[column] = "datetime"
            continue
        except (ValueError, TypeError):
            pass

        # Check if column is numeric
        if pd.api.types.is_numeric_dtype(df[column]):
            # Check if it's an integer or float
            if df[column].dtype in ["int32", "int64"]:
                type_mapping[column] = "integer"
            else:
                type_mapping[column] = "float"
        else:
            # Check if it's a categorical column
            unique_ratio = df[column].nunique() / len(df)
            if unique_ratio < 0.5:  # If less than 50% unique values
                type_mapping[column] = "categorical"
            else:
                type_mapping[column] = "text"

    return type_mapping


def validate_csv_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validates CSV data and returns a tuple (is_valid, error_list)."""
    errors = []

    # Check if there is data
    if df.empty:
        errors.append("The CSV file is empty")
        return False, errors

    # Check column names
    if df.columns.duplicated().any():
        errors.append("The file contains duplicate column names")

    # Check data type consistency
    data_types = detect_data_types(df)
    for column, dtype in data_types.items():
        if dtype in ["integer", "float"]:
            non_numeric = df[
                pd.to_numeric(df[column], errors="coerce").isna() & df[column].notna()
            ]
            if not non_numeric.empty:
                errors.append(f"Column {column} contains non-numeric values")

        elif dtype == "datetime":
            invalid_dates = df[
                pd.to_datetime(df[column], errors="coerce").isna() & df[column].notna()
            ]
            if not invalid_dates.empty:
                errors.append(f"Column {column} contains invalid dates")

    # Check percentage of missing values
    missing_percentages = (df.isnull().sum() / len(df)) * 100
    high_missing_cols = missing_percentages[missing_percentages > 50].index.tolist()
    if high_missing_cols:
        errors.append(
            f"The following columns have more than 50% missing values: {', '.join(high_missing_cols)}"
        )

    return len(errors) == 0, errors


def generate_data_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """Generates a detailed data profile."""
    profile = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "data_types": detect_data_types(df),
        "missing_values": df.isnull().sum().to_dict(),
        "missing_values_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
        "numeric_statistics": {},
        "categorical_statistics": {},
    }

    # Statistics for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if not numeric_cols.empty:
        profile["numeric_statistics"] = df[numeric_cols].describe().to_dict()

    # Statistics for categorical columns
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns
    for col in categorical_cols:
        profile["categorical_statistics"][col] = {
            "unique_values": df[col].nunique(),
            "frequent_values": df[col].value_counts().head(5).to_dict(),
        }

    return profile
