"""Regression tests for the population tree and chart data."""
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from data_loader import build_tree_from_csv
from region_tree import RegionTree
from visualization import _all_rows, _prediction_model_values


class PopulationProjectTests(unittest.TestCase):
    """Protect the data-model and visualization contracts."""

    def test_portfolio_dataset_loads_with_unique_plotly_identifiers(self) -> None:
        root = build_tree_from_csv(PROJECT_ROOT / 'cleaned_population_2006_2021_augmented.csv')
        root.update_aggregates()
        rows = _all_rows(root)
        self.assertEqual(len(rows), len({row['id'] for row in rows}))
        self.assertEqual(root.total_population(2021), 36_824_866.0)

    def test_loader_uses_geographic_code_to_keep_same_named_places_distinct(self) -> None:
        header = [
            'geographic_code', 'province', 'census_division', 'census_subdivision',
            'land_area_km2', 'population_2006', 'population_2011',
            'population_2016', 'population_2021'
        ]
        with tempfile.NamedTemporaryFile('w', newline='', suffix='.csv', delete=False) as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerow(['1111111', 'Test Province', 'Test Division', 'Springfield', 10, 1, 2, 3, 4])
            writer.writerow(['2222222', 'Test Province', 'Test Division', 'Springfield', 20, 5, 6, 7, 8])
            filename = file.name
        self.addCleanup(Path(filename).unlink)
        root = build_tree_from_csv(filename)
        root.update_aggregates()
        rows = _all_rows(root)
        self.assertEqual(len(rows), len({row['id'] for row in rows}))
        self.assertEqual(root.total_population(2021), 12.0)

    def test_prediction_is_never_negative_and_band_is_bounded(self) -> None:
        model = _prediction_model_values([2006, 2011, 2016, 2021], [100.0, 50.0, 10.0, 0.0])
        self.assertGreaterEqual(model['predicted_2026'], 0.0)
        self.assertGreaterEqual(model['lower'], 0.0)

    def test_invalid_area_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RegionTree('Invalid', 'subdivision', {2006: 1, 2011: 1, 2016: 1, 2021: 1}, -1)


if __name__ == '__main__':
    unittest.main()
