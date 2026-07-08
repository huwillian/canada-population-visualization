# Canada Population Visualization

This project is a Python-based data analysis and visualization program that models Canadian census geography using a tree data structure. It organizes population data into a hierarchy from Canada to provinces/territories, census divisions, and census subdivisions, then supports analysis of population density, population growth, regional comparisons, and simple population prediction.

## Project Overview

Raw census data is stored in flat CSV tables, which is not ideal for representing geographic hierarchy. This project cleans and reorganizes the data, builds a tree-based model of Canadian regions, and provides interactive visualizations for exploring population patterns over time.

The main idea is to represent Canadian regions as a tree:

```text
Canada
├── Province / Territory
│   ├── Census Division
│   │   ├── Census Subdivision
```

This structure makes it possible to use recursive methods for searching, aggregation, comparison, and visualization.

## Key Features

- Cleans and merges Canadian census population data from multiple years
- Builds a hierarchical `RegionTree` structure for Canadian geographic regions
- Uses recursive methods to search regions, aggregate population and land-area values, calculate density, and compare population growth
- Provides interactive Plotly visualizations, including treemaps, trend charts, ranking charts, and density charts
- Includes a Tkinter-based menu interface for selecting different analysis and visualization options
- Supports a simple 2026 population prediction based on historical census values

## Technologies Used

- Python
- Plotly
- Tkinter
- CSV data processing
- Tree data structures
- Recursion
- Basic linear regression

## Academic Context and Contributions

This project was originally completed as a CSC111 group project at the University of Toronto. This repository is a cleaned portfolio version of the project and does not include course instructions, grading materials, or private teammate information.

I contributed substantially to the project, especially in implementation-heavy areas such as the tree-based data model, data loading logic, recursive analysis methods, and visualization-related features. I also collaborated with teammates on design decisions and helped connect different parts of the project into a working application.

## Project Structure

```text
main.py                                      # Main entry point and Tkinter menu interface
region_tree.py                               # RegionTree class and core recursive analysis methods
data_loader.py                               # Converts cleaned CSV data into a RegionTree
visualization.py                             # Plotly charts, treemaps, rankings, trends, and prediction views
date_clean.py                                # Data cleaning and preprocessing workflow
cleaned_population_2006_2021_augmented.csv   # Cleaned project-ready population dataset
requirements.txt                             # Required Python packages
```

## How to Run

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Run the main program:

```bash
python main.py
```

A menu window will open. From there, users can choose different population visualizations and analysis views.

## Data Note

The dataset used in this project is based on Canadian census population data. This portfolio version includes the cleaned project-ready CSV file required to run the program. Large raw source files, review files, course instructions, and grading materials are not included.
