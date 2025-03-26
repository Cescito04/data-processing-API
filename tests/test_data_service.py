import unittest
import pandas as pd
from app.services.data_service import DataService
import os
import tempfile

class TestDataService(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for tests
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        self.data_service = DataService(self.temp_db.name)
        
        # Create test data
        self.test_data = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e'],
            'col3': [1.1, 2.2, 3.3, 4.4, 5.5]
        })

    def tearDown(self):
        # Clean up the temporary database
        self.temp_db.close()
        os.unlink(self.temp_db.name)

    def test_save_and_get_dataframe(self):
        # Test saving and retrieving data
        self.assertTrue(self.data_service.save_dataframe(self.test_data))
        retrieved_df = self.data_service.get_dataframe()
        pd.testing.assert_frame_equal(self.test_data, retrieved_df)

    def test_get_statistics(self):
        # Test statistics calculation
        self.data_service.save_dataframe(self.test_data)
        stats = self.data_service.get_statistics()
        self.assertIsNotNone(stats)
        self.assertIn('basic_stats', stats)
        self.assertIn('missing_values', stats)

    def test_filter_data(self):
        # Test data filtering
        self.data_service.save_dataframe(self.test_data)
        filtered_df = self.data_service.filter_data('col1', 3, 'greater_than')
        self.assertEqual(len(filtered_df), 2)
        self.assertTrue(all(filtered_df['col1'] > 3))

    def test_apply_transformations(self):
        # Test transformations
        self.data_service.save_dataframe(self.test_data)
        transformations = [{
            'operation': 'normalize',
            'column': 'col1'
        }]
        transformed_df = self.data_service.apply_transformations(transformations)
        self.assertIsNotNone(transformed_df)
        self.assertNotEqual(transformed_df['col1'].tolist(), self.test_data['col1'].tolist())

if __name__ == '__main__':
    unittest.main()