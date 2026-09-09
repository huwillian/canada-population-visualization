"""Define the RegionTree class, the core data structure of the project.

This module contains the main abstract representation used throughout the
project: a tree of Canadian census regions. Its purpose is not only to store
data, but also to organize the dataset in a way that naturally supports
hierarchical analysis.

The central idea behind this file is that Canada's census geography is
inherently nested. A subdivision belongs to a division, a division belongs to
a province or territory, and all of them belong to Canada. Representing the
dataset as a tree therefore makes the structure of the data match the real
structure of the regions.

Each RegionTree node stores:
- the name of the region
- the level of the region in the hierarchy
- population values for multiple census years
- land area
- a list of child subregions

Leaf nodes represent census subdivisions, which are the most detailed regions
in the dataset. These leaves store the direct population and land-area values
loaded from the CSV file. Internal nodes represent larger geographic units such
as provinces and census divisions.

A major design idea in this file is that internal nodes can be analyzed in the
same way as leaves after aggregate values are updated. The method
update_aggregates recursively combines the values of child nodes so that a
province, division, or the country itself can store total population and total
land area based on all descendants. This allows one consistent interface for
analysis across all levels of the tree.

This module also contains most of the project's computational logic. Instead of
putting analysis code inside the visualization file, the RegionTree class
provides methods that answer meaningful questions about the data, such as:
- finding a specific subregion
- computing total population and total area
- calculating density
- measuring absolute and percentage population change
- identifying the densest or fastest-growing direct child
- finding all high-density subdivision leaves
- collecting all regions at a given level
- measuring how much population is concentrated in the top k subdivisions
- computing density variance
- generating population and density trends across years
- ranking subregions by density or growth
- producing summary statistics for one region
- predicting future population using a simple linear regression model

This design keeps the project well structured. The RegionTree class acts as the
analytical engine of the project: it stores the hierarchical dataset and
provides reusable operations that later modules can call. Because the logic is
embedded in the data structure itself, the visualization and main modules can
focus on presentation and user interaction instead of repeating calculations.

In short, this file is the conceptual center of the whole project. It gives the
dataset a meaningful tree form and provides the recursive methods that make the
project more complex, more organized, and more aligned with the idea of using
trees as a core part of the program.
"""
from __future__ import annotations
from typing import Optional


YEARS = [2006, 2011, 2016, 2021]


class RegionTree:
    """A tree representing a geographic region in Canada.

    Instance Attributes:
        - name: the name of this region
        - level: the geographic level of this region
        - populations: a dictionary mapping census year to population
        - land_area: the land area of this region in square kilometres
        - subregions: the children of this region

    Representation Invariants:
        - self.level in {'country', 'province', 'division', 'subdivision'}
        - self.land_area >= 0
        - all(pop >= 0 for pop in self.populations.values())
    """
    name: str
    identifier: str
    level: str
    populations: dict[int, float]
    land_area: float
    subregions: list[RegionTree]

    def __init__(self, name: str, level: str,
                 populations: Optional[dict[int, float]] = None,
                 land_area: float = 0.0, identifier: Optional[str] = None) -> None:
        """Initialize a new region tree."""
        if level not in {'country', 'province', 'division', 'subdivision'}:
            raise ValueError(f'Unknown region level: {level}')
        if land_area < 0:
            raise ValueError('Land area cannot be negative.')
        self.name = name
        self.level = level
        self.identifier = identifier if identifier is not None else name

        if populations is None:
            self.populations = {year: 0.0 for year in YEARS}
        else:
            self.populations = populations.copy()

        if set(self.populations) != set(YEARS):
            raise ValueError('Population data must contain every supported census year.')
        if any(population < 0 for population in self.populations.values()):
            raise ValueError('Population values cannot be negative.')

        self.land_area = land_area
        self.subregions = []

    def add_subregion(self, subregion: RegionTree) -> None:
        """Add subregion as a child of this node."""
        self.subregions.append(subregion)

    def get_subregion(self, name: str) -> Optional[RegionTree]:
        """Return the direct child subregion with the given name.

        Return None if no direct child has that name.
        """
        for subregion in self.subregions:
            if subregion.name == name:
                return subregion
        return None

    def find_subregion(self, name: str) -> Optional[RegionTree]:
        """Return the region with the given name in this tree.

        Return None if no such region exists.
        """
        if self.name == name:
            return self

        for subregion in self.subregions:
            found = subregion.find_subregion(name)
            if found is not None:
                return found

        return None

    def total_population(self, year: int) -> float:
        """Return this region's total population for the given year."""
        return self.populations.get(year, 0.0)

    def total_area(self) -> float:
        """Return the total land area of this region."""
        if self.subregions == []:
            return self.land_area

        total = 0.0
        for subregion in self.subregions:
            total += subregion.total_area()
        return total

    def density(self, year: int) -> float:
        """Return the population density of this region for the given year."""
        if self.land_area == 0:
            return 0.0
        return self.total_population(year) / self.land_area

    def population_change(self, start_year: int, end_year: int) -> float:
        """Return the population change from start_year to end_year."""
        return self.total_population(end_year) - self.total_population(start_year)

    def population_change_pct(self, start_year: int, end_year: int) -> float:
        """Return the percentage population change from start_year to end_year."""
        start_pop = self.total_population(start_year)
        if start_pop == 0:
            return 0.0
        return (self.population_change(start_year, end_year) / start_pop) * 100

    def most_dense_subregion(self, year: int) -> Optional[RegionTree]:
        """Return the direct child with the highest density in the given year.

        Return None if this region has no subregions.
        """
        if self.subregions == []:
            return None

        densest = self.subregions[0]
        for subregion in self.subregions[1:]:
            if subregion.density(year) > densest.density(year):
                densest = subregion

        return densest

    def fastest_growing_subregion(self, start_year: int,
                                  end_year: int) -> Optional[RegionTree]:
        """Return the direct child with the largest population increase from
        start_year to end_year.

        Return None if this region has no subregions.
        """
        if self.subregions == []:
            return None

        fastest = self.subregions[0]
        for subregion in self.subregions[1:]:
            if (subregion.population_change(start_year, end_year)
                    > fastest.population_change(start_year, end_year)):
                fastest = subregion

        return fastest

    def find_high_density_cities(self, threshold: float,
                                 year: int) -> list[RegionTree]:
        """Return all subdivision nodes with density above threshold in year.

        The returned list is sorted in descending order of density.

        Preconditions:
            - threshold >= 0
        """
        if self.level == 'subdivision':
            if self.density(year) > threshold:
                return [self]
            return []

        high_density = []
        for subregion in self.subregions:
            high_density.extend(subregion.find_high_density_cities(threshold, year))

        high_density.sort(key=lambda region: region.density(year), reverse=True)
        return high_density

    def _all_subdivision_leaves(self) -> list[RegionTree]:
        """Return all subdivision leaves contained in this tree."""
        if self.level == 'subdivision':
            return [self]

        leaves = []
        for subregion in self.subregions:
            leaves.extend(subregion._all_subdivision_leaves())
        return leaves

    def all_subregions_at_level(self, level: str) -> list[RegionTree]:
        """Return all nodes in this tree whose level is equal to level.

        Preconditions:
            - level in {'country', 'province', 'division', 'subdivision'}
        """
        regions = []
        if self.level == level:
            regions.append(self)

        for subregion in self.subregions:
            regions.extend(subregion.all_subregions_at_level(level))

        return regions

    def top_k_population_coverage(self, year: int, k: int) -> float:
        """Return the fraction of this region's population contained in its
        k largest subdivisions in the given year.

        Preconditions:
            - k >= 1
        """
        leaves = self._all_subdivision_leaves()
        if leaves == []:
            return 0.0

        leaves.sort(key=lambda region: region.total_population(year), reverse=True)

        covered_population = 0.0
        for region in leaves[:k]:
            covered_population += region.total_population(year)

        total = self.total_population(year)
        if total == 0:
            return 0.0
        return covered_population / total

    def density_variance(self, year: int) -> float:
        """Return the variance of subdivision densities inside this region
        for the given year.

        Return 0.0 if there are fewer than 2 subdivision leaves.
        """
        leaves = self._all_subdivision_leaves()
        if len(leaves) < 2:
            return 0.0

        densities = []
        for region in leaves:
            densities.append(region.density(year))

        mean_density = sum(densities) / len(densities)

        squared_diffs = 0.0
        for density in densities:
            squared_diffs += (density - mean_density) ** 2

        return squared_diffs / len(densities)

    def population_trend(self) -> dict[int, float]:
        """Return this region's population for each census year."""
        return {year: self.total_population(year) for year in YEARS}

    def density_trend(self) -> dict[int, float]:
        """Return this region's density for each census year."""
        return {year: self.density(year) for year in YEARS}

    def year_to_year_changes(self) -> dict[str, float]:
        """Return population changes between consecutive census years."""
        changes = {}
        for i in range(len(YEARS) - 1):
            start = YEARS[i]
            end = YEARS[i + 1]
            changes[f'{start}-{end}'] = self.population_change(start, end)
        return changes

    def top_k_growing_subregions(self, start_year: int, end_year: int,
                                 level: str, k: int) -> list[RegionTree]:
        """Return the top k regions at the given level by population growth.

        Preconditions:
            - level in {'country', 'province', 'division', 'subdivision'}
            - k >= 1
        """
        regions = self.all_subregions_at_level(level)

        # Usually we do not want to include self if its level matches.
        if self in regions:
            regions.remove(self)

        regions.sort(
            key=lambda region: region.population_change(start_year, end_year),
            reverse=True
        )
        return regions[:k]

    def top_k_dense_subregions(self, year: int, level: str,
                               k: int) -> list[RegionTree]:
        """Return the top k regions at the given level by density.

        Preconditions:
            - level in {'country', 'province', 'division', 'subdivision'}
            - k >= 1
        """
        regions = self.all_subregions_at_level(level)

        if self in regions:
            regions.remove(self)

        regions.sort(
            key=lambda region: region.density(year),
            reverse=True
        )
        return regions[:k]

    def summary_stats(self, start_year: int, end_year: int,
                      density_year: int) -> dict[str, object]:
        """Return a dictionary of summary statistics for this region."""
        densest = self.most_dense_subregion(density_year)
        fastest = self.fastest_growing_subregion(start_year, end_year)

        return {
            'name': self.name,
            'level': self.level,
            'population_start': self.total_population(start_year),
            'population_end': self.total_population(end_year),
            'population_change': self.population_change(start_year, end_year),
            'population_change_pct': self.population_change_pct(start_year, end_year),
            'density': self.density(density_year),
            'total_area': self.total_area(),
            'densest_subregion': densest.name if densest is not None else None,
            'fastest_growing_subregion': fastest.name if fastest is not None else None
        }

    def update_aggregates(self) -> None:
        """Update this tree so that each internal node stores total populations
        and total land area of all its descendants.
        """
        if self.subregions == []:
            return

        for subregion in self.subregions:
            subregion.update_aggregates()

        self.populations = {census_year: 0.0 for census_year in YEARS}
        self.land_area = 0.0

        for subregion in self.subregions:
            for year in YEARS:
                self.populations[year] += subregion.populations.get(year, 0.0)
            self.land_area += subregion.land_area

    def predict_population(self, year: int) -> float:
        """Predict population for a future year using linear regression."""
        years = [2006, 2011, 2016, 2021]
        populations = [self.total_population(y) for y in years]

        n = len(years)
        mean_x = sum(years) / n
        mean_y = sum(populations) / n

        numerator = sum((years[i] - mean_x) * (populations[i] - mean_y)
                        for i in range(n))
        denominator = sum((years[i] - mean_x) ** 2 for i in range(n))

        if denominator == 0:
            return mean_y

        slope = numerator / denominator
        intercept = mean_y - slope * mean_x

        # Linear extrapolation is only a descriptive baseline. A population
        # count cannot be negative, so keep the result in a meaningful domain.
        return max(0.0, slope * year + intercept)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    import python_ta
    python_ta.check_all(config={
        'extra-imports': [],
        'allowed-io': [],
        'max-line-length': 100
    })
