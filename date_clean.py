"""Clean, reorganize, and merge raw census tables into one project-ready CSV.

This module handles the entire data-preparation stage of the project.
Its main purpose is to take raw Statistics Canada census files, which are
large, messy, and not organized in a way that is convenient for our program,
and transform them into one clean dataset with a consistent structure.

The overall idea of this file is to separate data cleaning from data analysis.
Instead of forcing later modules to work directly with raw census tables,
this module performs all preprocessing in advance and produces a simplified
CSV file that contains exactly the columns required by the project.

The code follows a staged workflow.

First, the module reads the raw 2021 census file. From this file, it extracts
the geographic hierarchy information and the most recent numeric values needed
for the project, including province names, census division names, census
subdivision names, land area, 2016 population, and 2021 population.

Second, the module reads the historical 2011 census file. This second file is
used to recover earlier population values, specifically the 2006 and 2011
population counts. Because the two raw files do not come in the same ready-made
format, this module uses geographic codes to match rows from the two datasets.

Third, after both data sources have been processed, the module merges them into
a single row format. Each merged row represents one census subdivision and
contains all values needed later by the tree and visualization modules:
province, census division, census subdivision, land area, and populations for
2006, 2011, 2016, and 2021.

A key design idea in this file is that it does not assume all raw rows are
usable. Some rows may have missing names, missing historical populations, or
missing land area values. For that reason, the module splits the merged rows
into two outputs:
- a final cleaned file containing rows that are ready for the project
- a review file containing incomplete rows that may need manual checking

This design makes the rest of the project much simpler and safer. Once this
module has produced the cleaned CSV, later files do not need to worry about
raw encodings, different source formats, code matching, or incomplete rows.
They can focus only on loading, organizing, analyzing, and visualizing clean
data.

In short, this module acts as the foundation of the whole project. It turns
messy census source data into a reliable input format that supports the
tree-based structure and all later visual analysis.
"""
from __future__ import annotations
import csv


RAW_2021_FILE = '98100002.csv'
RAW_2011_FILE = '98-310-XWE2011002-301.CSV'
OUTPUT_FILE = 'cleaned_population_2006_2021.csv'
REVIEW_FILE = 'needs_review_2006_2021.csv'


def read_csv_file(filename: str, encoding: str, skiprows: int = 0) -> list[list[str]]:
    """Read a CSV file and return its contents as a list of rows."""
    with open(filename, 'r', encoding=encoding, newline='') as csv_file:
        reader = csv.reader(csv_file)
        rows = list(reader)
    return rows[skiprows:]


def write_csv_file(filename: str, rows: list[list[object]], encoding: str) -> None:
    """Write rows to a CSV file."""
    with open(filename, 'w', encoding=encoding, newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(rows)


def safe_get(row: list[str], index: int) -> str:
    """Return row[index] if possible, or '' if index is out of range."""
    if 0 <= index < len(row):
        return row[index]
    return ''


def to_number(value: str) -> float | None:
    """Convert a string to a number.

    Return None if conversion fails or the string is empty.
    """
    cleaned = value.strip().replace(',', '')
    if cleaned == '':
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def format_number(value: float | None) -> str:
    """Return a CSV-friendly string for a number."""
    if value is None:
        return ''
    if value.is_integer():
        return str(int(value))
    return str(value)


def get_column_indices(header: list[str], needed_columns: list[str]) -> dict[str, int]:
    """Return a mapping from column name to index."""
    indices = {}
    for column in needed_columns:
        indices[column] = header.index(column)
    return indices


def _extract_population_values(
        row_2021: list[str], index_2021: dict[str, int]
) -> tuple[float | None, float | None, float | None]:
    """Extract 2021/2016 population and land area from one 2021-row."""
    population_2021 = to_number(
        safe_get(row_2021, index_2021['Population and dwelling counts (13): Population, 2021 [1]'])
    )
    population_2016 = to_number(
        safe_get(row_2021, index_2021['Population and dwelling counts (13): Population, 2016 [2]'])
    )
    land_area_key = (
        'Population and dwelling counts (13): '
        'Land area in square kilometres, 2021 [10]'
    )
    land_area_km2 = to_number(
        safe_get(
            row_2021,
            index_2021[land_area_key]
        )
    )
    return population_2021, population_2016, land_area_km2


def _load_2021_base_rows() -> list[dict[str, object]]:
    """Read the 2021/2016 table and return base subdivision rows."""
    rows_2021 = read_csv_file(RAW_2021_FILE, encoding='utf-8-sig')
    index_2021 = get_column_indices(rows_2021[0], [
        'DGUID',
        'GEO',
        'Population and dwelling counts (13): Population, 2021 [1]',
        'Population and dwelling counts (13): Population, 2016 [2]',
        'Population and dwelling counts (13): Land area in square kilometres, 2021 [10]'
    ])
    data_2021 = rows_2021[1:]

    code_maps: dict[str, dict[str, str]] = {'province': {}, 'division': {}}
    for row_2021 in data_2021:
        dguid = safe_get(row_2021, index_2021['DGUID'])
        geo = safe_get(row_2021, index_2021['GEO'])
        if dguid.startswith('2021A0002'):
            code_maps['province'][dguid[-2:]] = geo
        elif dguid.startswith('2021A0003'):
            code_maps['division'][dguid[-4:]] = geo

    base_rows: list[dict[str, object]] = []
    for row_2021 in data_2021:
        dguid = safe_get(row_2021, index_2021['DGUID'])
        if not dguid.startswith('2021A0005'):
            continue

        csd_code = dguid[-7:]
        population_2021, population_2016, land_area_km2 = _extract_population_values(
            row_2021, index_2021
        )

        base_rows.append({
            'csd_code': csd_code,
            'province': code_maps['province'].get(csd_code[:2]),
            'census_division': code_maps['division'].get(csd_code[:4]),
            'census_subdivision': safe_get(row_2021, index_2021['GEO']),
            'land_area_km2': land_area_km2,
            'population_2016': population_2016,
            'population_2021': population_2021
        })
    return base_rows


def _load_2011_historical_dict() -> dict[str, dict[str, float | None]]:
    """Read the 2011/2006 table and return historical population mapping."""
    rows_2011 = read_csv_file(RAW_2011_FILE, encoding='latin1', skiprows=1)
    index_2011 = get_column_indices(
        rows_2011[0], ['Geographic code', 'Population, 2011', 'Population, 2006']
    )
    historical_dict: dict[str, dict[str, float | None]] = {}
    for row_2011 in rows_2011[1:]:
        geographic_code = safe_get(row_2011, index_2011['Geographic code']).strip()
        if len(geographic_code) != 7:
            continue
        historical_dict[geographic_code] = {
            'population_2006': to_number(safe_get(row_2011, index_2011['Population, 2006'])),
            'population_2011': to_number(safe_get(row_2011, index_2011['Population, 2011']))
        }
    return historical_dict


def _load_raw_data() -> tuple[list[dict[str, object]], dict[str, dict[str, float | None]]]:
    """Read raw CSV data and return base rows plus historical population data."""
    base_rows = _load_2021_base_rows()
    historical_dict = _load_2011_historical_dict()
    return base_rows, historical_dict


def _merge_rows(
        base_rows: list[dict[str, object]],
        historical_dict: dict[str, dict[str, float | None]]) -> list[dict[str, object]]:
    """Merge base rows with historical population data by CSD code."""
    merged_rows: list[dict[str, object]] = []
    for base_row in base_rows:
        csd_code = str(base_row['csd_code'])
        historical = historical_dict.get(csd_code)
        if historical is None:
            population_2006 = None
            population_2011 = None
        else:
            population_2006 = historical['population_2006']
            population_2011 = historical['population_2011']

        merged_rows.append({
            'province': base_row['province'],
            'census_division': base_row['census_division'],
            'census_subdivision': base_row['census_subdivision'],
            'land_area_km2': base_row['land_area_km2'],
            'population_2006': population_2006,
            'population_2011': population_2011,
            'population_2016': base_row['population_2016'],
            'population_2021': base_row['population_2021']
        })
    return merged_rows


def _format_output_rows(row: dict[str, object]) -> list[object]:
    """Convert one merged dictionary row into CSV output row format."""
    land_area = row['land_area_km2']
    population_2006 = row['population_2006']
    population_2011 = row['population_2011']
    population_2016 = row['population_2016']
    population_2021 = row['population_2021']

    return [
        '' if row['province'] is None else str(row['province']),
        '' if row['census_division'] is None else str(row['census_division']),
        '' if row['census_subdivision'] is None else str(row['census_subdivision']),
        format_number(land_area if isinstance(land_area, float) else None),
        format_number(population_2006 if isinstance(population_2006, float) else None),
        format_number(population_2011 if isinstance(population_2011, float) else None),
        format_number(population_2016 if isinstance(population_2016, float) else None),
        format_number(population_2021 if isinstance(population_2021, float) else None)
    ]


def _split_review_and_clean(
        merged_rows: list[dict[str, object]]
) -> tuple[list[list[object]], list[list[object]], int, int]:
    """Split merged rows into review output and final clean output."""
    header: list[object] = [
        'province',
        'census_division',
        'census_subdivision',
        'land_area_km2',
        'population_2006',
        'population_2011',
        'population_2016',
        'population_2021'
    ]
    review_output: list[list[object]] = [header]
    final_output: list[list[object]] = [header]
    review_count = 0
    final_count = 0

    for merged_row in merged_rows:
        output_row = _format_output_rows(merged_row)

        needs_review = (
            merged_row['population_2006'] is None
            or merged_row['population_2011'] is None
            or merged_row['province'] is None
            or merged_row['census_division'] is None
            or merged_row['land_area_km2'] is None
        )
        if needs_review:
            review_output.append(output_row)
            review_count += 1

        has_all_needed_values = (
            merged_row['province'] is not None
            and merged_row['census_division'] is not None
            and merged_row['census_subdivision'] is not None
            and merged_row['land_area_km2'] is not None
            and merged_row['population_2006'] is not None
            and merged_row['population_2011'] is not None
            and merged_row['population_2016'] is not None
            and merged_row['population_2021'] is not None
        )
        land_area = merged_row['land_area_km2']
        if has_all_needed_values and isinstance(land_area, float) and land_area > 0:
            final_output.append(output_row)
            final_count += 1

    return final_output, review_output, final_count, review_count


def build_cleaned_population_csv() -> None:
    """Build a cleaned multi-year population CSV for 2006, 2011, 2016, 2021."""
    base_rows, historical_dict = _load_raw_data()
    merged_rows: list[dict[str, object]] = _merge_rows(base_rows, historical_dict)
    final_output, review_output, *_ = _split_review_and_clean(merged_rows)

    write_csv_file(REVIEW_FILE, review_output, encoding='utf-8-sig')
    write_csv_file(OUTPUT_FILE, final_output, encoding='utf-8-sig')


def main() -> None:
    """Run the multi-year CSV cleaning workflow."""
    build_cleaned_population_csv()


if __name__ == '__main__':
    main()
    import doctest
    doctest.testmod()
    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['csv', 'doctest', 'python_ta'],
        'allowed-io': ['read_csv_file', 'write_csv_file'],
        'max-line-length': 100
    })
