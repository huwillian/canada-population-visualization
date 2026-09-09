# Canada Population Visualization

An interactive Python project for exploring Canadian census population data from 2006 to 2021. It represents census geography as a tree—Canada, province or territory, census division, then census subdivision—and uses Plotly to present population, density, growth, and trend comparisons.

## What it offers

- Interactive density and population-change treemaps with province/territory selection
- Population and density trends for Canada and each province or territory
- Rankings for dense, fast-growing, and high-density census subdivisions
- A compact text summary for a selected region
- A clearly labelled 2026 linear baseline based on the four available censuses

## Run it

Use Python 3.10 or later.

```bash
python -m pip install -r requirements.txt
python main.py
```

The program locates its packaged dataset relative to `main.py`, so it can be started from any working directory.

## Data and interpretation

`cleaned_population_2006_2021_augmented.csv` contains 4,907 cleaned census-subdivision records with population values for 2006, 2011, 2016, and 2021. It is a portfolio-ready derived dataset based on Canadian census tables.

The included data is suitable for exploring the published hierarchy and comparisons in this repository. It should not be used as a current official national population estimate: geographic boundaries and census definitions can change between censuses, and the repository does not include the raw source tables needed to reproduce a full boundary reconciliation.

The data-cleaning script expects those raw tables locally and now writes the same `cleaned_population_2006_2021_augmented.csv` filename used by the application. When raw data is regenerated, it retains the seven-digit census-subdivision geographic code. The loader uses that code as the permanent chart identifier, which prevents similarly named places from colliding in treemaps. The legacy bundled CSV has no code column; it remains supported with a deterministic record identifier.

The 2026 chart is an exploratory linear trend extrapolation, not an official forecast. Its band shows historical fit dispersion and is explicitly not a confidence interval. Negative extrapolations are bounded at zero because population counts cannot be negative.

## Project layout

```text
main.py                         Tkinter launch menu
data_loader.py                  CSV validation and RegionTree construction
region_tree.py                  Tree storage, aggregation, analysis, and baseline prediction
visualization.py                Interactive Plotly figures
date_clean.py                   Optional raw-data cleaning workflow
cleaned_population_2006_2021_augmented.csv
tests/test_project.py           Regression tests
```

## Quality checks

```bash
python -m unittest discover -s tests -v
```

The test suite verifies the packaged dataset loads, every Plotly node identifier is unique, same-named geographic records remain separate when geographic codes are available, invalid input is rejected, and the prediction baseline cannot become negative. GitHub Actions runs the same suite for pushes and pull requests.

## Background

This was originally a CSC111 group project at the University of Toronto. This repository is a portfolio version and excludes course materials, grading artifacts, raw source files, and private teammate information.
