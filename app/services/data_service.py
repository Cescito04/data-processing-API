from typing import Dict, List, Any, Optional
import pandas as pd
import sqlite3
from ..utils.data_processing import (
    validate_dataframe,
    calculate_advanced_stats,
    filter_dataframe,
    transform_data
)

class DataService:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def save_dataframe(self, df: pd.DataFrame, table_name: str = 'data_table') -> bool:
        """Sauvegarde un DataFrame dans la base de données SQLite."""
        if not validate_dataframe(df):
            return False
        
        try:
            with sqlite3.connect(self.database_url) as conn:
                df.to_sql(table_name, conn, if_exists='replace', index=False)
            return True
        except Exception:
            return False

    def get_dataframe(self, table_name: str = 'data_table') -> Optional[pd.DataFrame]:
        """Récupère les données de la base de données sous forme de DataFrame."""
        try:
            with sqlite3.connect(self.database_url) as conn:
                return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        except Exception:
            return None

    def get_statistics(self, table_name: str = 'data_table') -> Optional[Dict[str, Any]]:
        """Calcule les statistiques sur les données."""
        df = self.get_dataframe(table_name)
        if df is None:
            return None
        return calculate_advanced_stats(df)

    def filter_data(self, column: str, value: Any, operator: str = 'equals',
                    table_name: str = 'data_table') -> Optional[pd.DataFrame]:
        """Filtre les données selon les critères spécifiés."""
        df = self.get_dataframe(table_name)
        if df is None:
            return None
        try:
            return filter_dataframe(df, column, value, operator)
        except Exception:
            return None

    def apply_transformations(self, transformations: List[Dict[str, Any]],
                            table_name: str = 'data_table') -> Optional[pd.DataFrame]:
        """Applique une série de transformations aux données."""
        df = self.get_dataframe(table_name)
        if df is None:
            return None
        try:
            return transform_data(df, transformations)
        except Exception:
            return None