import pandas as pd
from typing import Dict, List, Any, Optional
import numpy as np
from .csv_validator import detect_data_types, validate_csv_data
from .data_processing import (
    handle_missing_values,
    handle_outliers,
    remove_duplicates,
    normalize_data,
)


class CSVProcessor:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.original_df = df.copy()
        self.processing_history = []

    def auto_clean(self) -> pd.DataFrame:
        """Performs automatic data cleaning."""
        # Detect data types
        data_types = detect_data_types(self.df)

        # Process numeric columns
        numeric_cols = [
            col for col, dtype in data_types.items() if dtype in ["integer", "float"]
        ]
        if numeric_cols:
            # Handle missing numeric values
            self.df = handle_missing_values(
                self.df, strategy="mean", columns=numeric_cols
            )
            # Handle outliers
            self.df = handle_outliers(self.df, method="iqr", columns=numeric_cols)
            # Normalize numeric data
            self.df = normalize_data(self.df, method="minmax", columns=numeric_cols)

            self.processing_history.append(
                {"operation": "auto_clean_numeric", "columns": numeric_cols}
            )

        # Process categorical columns
        categorical_cols = [
            col for col, dtype in data_types.items() if dtype == "categorical"
        ]
        if categorical_cols:
            # Handle missing categorical values
            self.df = handle_missing_values(
                self.df, strategy="mode", columns=categorical_cols
            )

            self.processing_history.append(
                {"operation": "auto_clean_categorical", "columns": categorical_cols}
            )

        # Process datetime columns
        datetime_cols = [
            col for col, dtype in data_types.items() if dtype == "datetime"
        ]
        if datetime_cols:
            for col in datetime_cols:
                self.df[col] = pd.to_datetime(self.df[col], errors="coerce")
                # Replace invalid dates with NaT
                self.df[col] = self.df[col].fillna(pd.NaT)

            self.processing_history.append(
                {"operation": "auto_clean_datetime", "columns": datetime_cols}
            )

        # Remove duplicates
        original_len = len(self.df)
        self.df = remove_duplicates(self.df)
        if len(self.df) < original_len:
            self.processing_history.append(
                {
                    "operation": "remove_duplicates",
                    "rows_removed": original_len - len(self.df),
                }
            )

        return self.df

    def get_processing_summary(self) -> Dict[str, Any]:
        """Generates a summary of processing operations performed."""
        return {
            "operations_count": len(self.processing_history),
            "operations": self.processing_history,
            "initial_rows": len(self.original_df),
            "final_rows": len(self.df),
            "modified_columns": list(
                set(
                    [
                        col
                        for op in self.processing_history
                        for col in op.get("columns", [])
                    ]
                )
            ),
        }

    def revert_changes(self):
        """Cancels all modifications and returns to original data."""
        self.df = self.original_df.copy()
        self.processing_history = []

    def export_to_csv(self, output_path: str) -> bool:
        """Exports processed data to a CSV file."""
        try:
            self.df.to_csv(output_path, index=False)
            return True
        except Exception:
            return False

    def get_data_quality_score(self) -> Dict[str, float]:
        """Calculates a data quality score."""
        scores = {
            "completeness": (
                1 - self.df.isnull().sum().sum() / (self.df.shape[0] * self.df.shape[1])
            )
            * 100,
            "uniqueness": (1 - len(self.df[self.df.duplicated()]) / len(self.df)) * 100,
        }

        # Score for data type consistency
        data_types = detect_data_types(self.df)
        type_consistency = 0
        for col, dtype in data_types.items():
            if dtype in ["integer", "float"]:
                type_consistency += 1 - pd.to_numeric(
                    self.df[col], errors="coerce"
                ).isna().sum() / len(self.df)
            elif dtype == "datetime":
                type_consistency += 1 - pd.to_datetime(
                    self.df[col], errors="coerce"
                ).isna().sum() / len(self.df)

        scores["type_consistency"] = (type_consistency / len(data_types)) * 100
        scores["overall_quality"] = sum(scores.values()) / len(scores)

        return scores
