from typing import Dict, List, Any, Optional
import pandas as pd
import sqlite3
from ..utils.data_processing import (
    validate_dataframe,
    calculate_advanced_stats,
    filter_dataframe,
    transform_data,
)
from ..utils.json_processor import (
    load_json_data,
    save_json_data,
    process_json_data,
)


class DataService:
    def __init__(self, database_url: str):
        """Initialise le service de données avec l'URL de la base de données."""
        self.database_url = database_url

    def process_json_file(self, json_file_path: str, transformations: List[Dict[str, Any]] = None) -> Optional[pd.DataFrame]:
        """Traite un fichier JSON et retourne un DataFrame."""
        df = load_json_data(json_file_path)
        if df is not None and transformations:
            df = transform_data(df, transformations)
        return df

    def save_to_json(self, df: pd.DataFrame, json_file_path: str) -> bool:
        """Sauvegarde un DataFrame au format JSON."""
        return save_json_data(df, json_file_path)

    def __init__(self, database_url: str):
        self.database_url = database_url

    def save_dataframe(self, df: pd.DataFrame, table_name: str = "data_table") -> bool:
        """Saves a DataFrame to the SQLite database."""
        if not validate_dataframe(df):
            return False

        try:
            with sqlite3.connect(self.database_url) as conn:
                df.to_sql(table_name, conn, if_exists="replace", index=False)
            return True
        except Exception:
            return False

    def get_dataframe(self, table_name: str = "data_table") -> Optional[pd.DataFrame]:
        """Retrieves data from the database as a DataFrame."""
        try:
            with sqlite3.connect(self.database_url) as conn:
                return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        except Exception:
            return None

    def get_statistics(
        self, table_name: str = "data_table"
    ) -> Optional[Dict[str, Any]]:
        """Calculates statistics on the data."""
        try:
            df = self.get_dataframe(table_name)
            if df is None or df.empty:
                return None
            if not any(df.select_dtypes(include=["number"]).columns):
                return {
                    "basic_stats": {"count": len(df)},
                    "correlations": {},
                    "missing_values": df.isnull().sum().to_dict(),
                    "unique_values": {col: df[col].nunique() for col in df.columns},
                }
            return calculate_advanced_stats(df)
        except Exception as e:
            print(f"Error calculating statistics: {str(e)}")
            return None

    def filter_data(
        self,
        column: str,
        value: Any,
        operator: str = "equals",
        table_name: str = "data_table",
    ) -> Optional[pd.DataFrame]:
        """Filters the data according to specified criteria."""
        df = self.get_dataframe(table_name)
        if df is None:
            return None
        try:
            return filter_dataframe(df, column, value, operator)
        except Exception:
            return None

    def apply_transformations(
        self, transformations: List[Dict[str, Any]], table_name: str = "data_table"
    ) -> Optional[pd.DataFrame]:
        """Applies a series of transformations to the data."""
        df = self.get_dataframe(table_name)
        if df is None:
            return None
        try:
            return transform_data(df, transformations)
        except Exception:
            return None
