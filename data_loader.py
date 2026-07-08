"""Load the cleaned CSV file and convert it into a hierarchical RegionTree.

This module is responsible for turning tabular census data into the tree
structure used by the rest of the project. The cleaned CSV file contains
all required information, but it is still stored as a flat sequence of rows.
Each row describes one census subdivision, which is useful for storage, but
not ideal for representing the geographic hierarchy of Canada.

The purpose of this file is to bridge that gap. It reads the cleaned CSV row
by row and builds a RegionTree that reflects the real nested structure of the
dataset:
Canada -> province/territory -> census division -> census subdivision.

The main code idea is incremental tree construction. As each row is read, the
module does not create a completely new branch blindly. Instead, it first
checks whether the corresponding province node already exists under the root.
If not, it creates that node. Then it does the same for the census division
under that province. Finally, it creates the census subdivision node as a leaf
and stores that row's land area and population dictionary inside it.

This design is important because the cleaned CSV contains repeated province and
division names across many rows. Reusing existing internal nodes ensures that
the final structure is a proper tree rather than a collection of duplicated
branches.

Another important role of this module is separation of concerns. The cleaning
module is responsible for preparing correct rows, and the RegionTree class is
responsible for storing and analyzing hierarchical data. This module sits in
between them and handles only the conversion process from one form to the other.

As a result, the rest of the project never has to work directly with CSV rows.
Once this module finishes, later modules can use tree methods such as recursive
search, aggregation, density calculation, and population comparison without
worrying about file format details.

In short, this file transforms clean but flat census data into the structured
tree model that makes the rest of the project possible.
"""
from __future__ import annotations
import csv


from region_tree import RegionTree


YEARS = [2006, 2011, 2016, 2021]


def build_tree_from_csv(filepath: str) -> RegionTree:
    """Return a RegionTree built from the given cleaned CSV file.

    The CSV file must contain these columns:
        province
        census_division
        census_subdivision
        land_area_km2
        population_2006
        population_2011
        population_2016
        population_2021
    """
    root = RegionTree('Canada', 'country')

    with open(filepath, 'r', encoding='utf-8-sig') as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            province_name = row['province'].strip()
            division_name = row['census_division'].strip()
            subdivision_name = row['census_subdivision'].strip()
            land_area = float(row['land_area_km2'])

            populations = {}
            for year in YEARS:
                populations[year] = float(row[f'population_{year}'])

            province_node = root.get_subregion(province_name)
            if province_node is None:
                province_node = RegionTree(province_name, 'province')
                root.add_subregion(province_node)

            division_node = province_node.get_subregion(division_name)
            if division_node is None:
                division_node = RegionTree(division_name, 'division')
                province_node.add_subregion(division_node)

            subdivision_node = RegionTree(
                subdivision_name,
                'subdivision',
                populations,
                land_area
            )
            division_node.add_subregion(subdivision_node)

    return root


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['csv', 'region_tree', 'python_ta'],
        'allowed-io': ['build_tree_from_csv'],
        'max-line-length': 100
    })
