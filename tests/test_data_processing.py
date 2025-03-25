import unittest
import pandas as pd
import numpy as np
from app.utils.data_processing import (
    validate_dataframe,
    get_numeric_columns,
    get_categorical_columns,
    calculate_advanced_stats,
    filter_dataframe,
    handle_missing_values,
    handle_outliers,
    remove_duplicates,
    normalize_data,
    transform_data
)

class TestDataProcessing(unittest.TestCase):
    def setUp(self):
        # Créer des données de test
        self.test_data = pd.DataFrame({
            'numeric1': [1, 2, 3, np.nan, 5],
            'numeric2': [1.1, 2.2, 3.3, 4.4, 5.5],
            'category': ['A', 'B', 'A', 'C', 'B'],
            'text': ['x', 'y', 'z', 'x', 'y']
        })

        # Données avec doublons
        self.data_with_duplicates = pd.DataFrame({
            'id': [1, 2, 2, 3],
            'value': ['a', 'b', 'b', 'c']
        })

        # Données avec valeurs aberrantes
        self.data_with_outliers = pd.DataFrame({
            'values': [1, 2, 3, 100, 2, 3, 1, 200]
        })

    def test_validate_dataframe(self):
        self.assertTrue(validate_dataframe(self.test_data))
        self.assertFalse(validate_dataframe(pd.DataFrame()))

    def test_get_numeric_columns(self):
        numeric_cols = get_numeric_columns(self.test_data)
        self.assertEqual(set(numeric_cols), {'numeric1', 'numeric2'})

    def test_get_categorical_columns(self):
        cat_cols = get_categorical_columns(self.test_data)
        self.assertEqual(set(cat_cols), {'category', 'text'})

    def test_calculate_advanced_stats(self):
        stats = calculate_advanced_stats(self.test_data)
        self.assertIn('basic_stats', stats)
        self.assertIn('correlations', stats)
        self.assertIn('missing_values', stats)
        self.assertIn('unique_values', stats)

    def test_filter_dataframe(self):
        # Test equals
        filtered = filter_dataframe(self.test_data, 'category', 'A')
        self.assertEqual(len(filtered), 2)

        # Test greater_than
        filtered = filter_dataframe(self.test_data, 'numeric2', 3.0, 'greater_than')
        self.assertEqual(len(filtered), 2)

        # Test contains
        filtered = filter_dataframe(self.test_data, 'text', 'x', 'contains')
        self.assertEqual(len(filtered), 2)

    def test_handle_missing_values(self):
        # Test mean strategy
        df_mean = handle_missing_values(self.test_data, strategy='mean')
        self.assertFalse(df_mean['numeric1'].isnull().any())
        self.assertEqual(df_mean['numeric1'].iloc[3], self.test_data['numeric1'].mean())

        # Test median strategy
        df_median = handle_missing_values(self.test_data, strategy='median')
        self.assertEqual(df_median['numeric1'].iloc[3], self.test_data['numeric1'].median())

        # Test mode strategy
        df_mode = handle_missing_values(self.test_data, strategy='mode')
        self.assertFalse(df_mode['numeric1'].isnull().any())

    def test_handle_outliers(self):
        # Test IQR method
        df_iqr = handle_outliers(self.data_with_outliers, method='iqr')
        self.assertTrue(df_iqr['values'].max() < 100)

        # Test Z-score method
        df_zscore = handle_outliers(self.data_with_outliers, method='zscore')
        self.assertTrue(df_zscore['values'].max() < 100)

    def test_remove_duplicates(self):
        df_no_dupes = remove_duplicates(self.data_with_duplicates)
        self.assertEqual(len(df_no_dupes), 3)

        # Test with subset
        df_no_dupes_subset = remove_duplicates(self.data_with_duplicates, subset=['value'])
        self.assertEqual(len(df_no_dupes_subset), 3)

    def test_normalize_data(self):
        # Test MinMax normalization
        df_minmax = normalize_data(self.test_data, method='minmax')
        self.assertTrue(all(df_minmax['numeric2'].between(0, 1)))

        # Test Z-score normalization
        df_zscore = normalize_data(self.test_data, method='zscore')
        self.assertAlmostEqual(df_zscore['numeric2'].mean(), 0, places=10)
        self.assertAlmostEqual(df_zscore['numeric2'].std(), 1, places=10)

    def test_transform_data(self):
        transformations = [
            {'operation': 'handle_missing', 'strategy': 'mean'},
            {'operation': 'normalize', 'method': 'minmax', 'columns': ['numeric2']},
            {'operation': 'one_hot_encode', 'column': 'category'}
        ]
        
        transformed_df = transform_data(self.test_data, transformations)
        
        # Vérifier que les valeurs manquantes sont traitées
        self.assertFalse(transformed_df['numeric1'].isnull().any())
        
        # Vérifier la normalisation
        self.assertTrue(all(transformed_df['numeric2'].between(0, 1)))
        
        # Vérifier l'encodage one-hot
        self.assertIn('category_A', transformed_df.columns)
        self.assertIn('category_B', transformed_df.columns)
        self.assertIn('category_C', transformed_df.columns)

if __name__ == '__main__':
    unittest.main()