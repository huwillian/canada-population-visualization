"""Build the visual and interactive output for the Canada population project.

This module contains the visualization layer of the project. Its purpose is to
take the hierarchical and analytical information stored in RegionTree objects
and turn it into charts, treemaps, and summary displays that users can explore.

The key design idea in this file is that tree data is powerful for analysis,
but not always in the exact format needed by a plotting library. Because of
that, this module does not simply call plotting functions directly on the tree.
Instead, it first transforms the tree into intermediate structures that are
easy for Plotly to use.

One important helper function flattens a RegionTree into a row-like structure.
This step makes it possible to build treemaps using ids, parent ids, labels,
values, and custom hover data. In other words, this file translates the
recursive tree representation into a visualization-friendly representation.

The module supports several different kinds of visual analysis.

Some functions focus on spatial hierarchy:
- density treemaps use area and colour to show how population and density are
  distributed across Canada and its subregions
- population change treemaps show how population has increased or decreased
  across different time intervals

Other functions focus on comparison and ranking:
- bar charts compare population change in absolute terms or percentage terms
- top-density and top-growth charts rank the most extreme regions
- high-density charts filter for regions above a threshold

Other functions focus on trends across time:
- population trend charts show long-term population change
- density trend charts show how regional density changes over multiple census
  years
- yearly change charts summarize changes between consecutive census periods

This module also includes a prediction component. Using historical population
data stored in the tree, it computes simple linear regression values and builds
an interactive chart that shows actual historical data, the fitted regression
line, and a predicted 2026 value.

A second important design idea is that this file keeps interface-specific logic
inside the visualization layer. Dropdown menus, trace visibility, hover text,
treemap colouring, and chart titles are all handled here rather than being
mixed into the RegionTree class. This keeps the project modular:
- RegionTree is responsible for storing and analyzing data
- this module is responsible for presenting results to the user

Overall, this file acts as the presentation engine of the project. It makes the
tree-based analysis visible, interactive, and easier to interpret by converting
structured data into meaningful visual forms.
"""
from __future__ import annotations
from typing import TypedDict

import plotly.graph_objects as go

from region_tree import RegionTree


class PredictionModel(TypedDict):
    """Regression and prediction values for population chart."""
    slope: float
    intercept: float
    predicted_2026: float
    extended_years: list[int]
    fitted_values: list[float]
    upper: float
    lower: float


def _selectable_regions(root: RegionTree) -> list[RegionTree]:
    """Return the regions that appear in dropdown menus.

    To keep the interface manageable, we use:
        - Canada
        - all provinces / territories

    You can extend this later if you want more options.
    """
    return [root] + root.subregions


def _all_rows(root: RegionTree) -> list[dict]:
    """Return a flattened list of rows for every node in the tree."""
    rows = []

    def _helper(node: RegionTree, parent_id: str, parent_name: str) -> None:
        node_id = node.identifier

        row = {
            'id': node_id,
            'parent': parent_id,
            'name': node.name,
            'parent_name': parent_name,
            'level': node.level,
            'land_area': node.total_area(),
            'population_2006': node.total_population(2006),
            'population_2011': node.total_population(2011),
            'population_2016': node.total_population(2016),
            'population_2021': node.total_population(2021),
            'population_2026': node.predict_population(2026),
            'density_2006': node.density(2006),
            'density_2011': node.density(2011),
            'density_2016': node.density(2016),
            'density_2021': node.density(2021),
            'change_2006_2021': node.population_change(2006, 2021),
            'change_pct_2006_2021': node.population_change_pct(2006, 2021),
        }
        rows.append(row)

        for subregion in node.subregions:
            _helper(subregion, node_id, node.name)

    _helper(root, '', '')
    return rows


def make_density_treemap(root: RegionTree) -> None:
    """Display an interactive treemap for 2021 density.

    Interface:
        - dropdown to switch between Canada and each province/territory
    Treemap settings:
        - area = 2021 population
        - color = 2021 density
    """
    selectable = _selectable_regions(root)

    fig = go.Figure()

    for i, region in enumerate(selectable):
        rows = _all_rows(region)

        ids = [row['id'] for row in rows]
        parents = [row['parent'] for row in rows]
        labels = [row['name'] for row in rows]
        values = [max(row['population_2021'], 0.0) for row in rows]
        colors = [row['density_2021'] for row in rows]

        customdata = [
            [
                row['level'],
                row['parent_name'],
                row['population_2006'],
                row['population_2011'],
                row['population_2016'],
                row['population_2021'],
                row['population_2026'],
                row['change_2006_2021'],
                row['change_pct_2006_2021'],
                row['land_area'],
                row['density_2021']
            ]
            for row in rows
        ]

        fig.add_trace(go.Treemap(
            ids=ids,
            parents=parents,
            labels=labels,
            values=values,
            branchvalues='total',
            customdata=customdata,
            marker={
                'colors': colors,
                'colorscale': 'Viridis',
                'colorbar': {'title': 'Density 2021'}
            },
            hovertemplate=(
                '<b>%{label}</b><br>'
                'Level: %{customdata[0]}<br>'
                'Parent: %{customdata[1]}<br>'
                'Population 2006: %{customdata[2]:,.0f}<br>'
                'Population 2011: %{customdata[3]:,.0f}<br>'
                'Population 2016: %{customdata[4]:,.0f}<br>'
                'Population 2021: %{customdata[5]:,.0f}<br>'
                '2026 linear baseline: %{customdata[6]:,.0f}<br>'
                'Change 2006→2021: %{customdata[7]:,.0f}<br>'
                'Change % 2006→2021: %{customdata[8]:,.2f}%<br>'
                'Land area: %{customdata[9]:,.2f} km²<br>'
                'Density 2021: %{customdata[10]:,.2f} people/km²'
                '<extra></extra>'
            ),
            visible=(i == 0)
        ))

    region_buttons = []
    for i, region in enumerate(selectable):
        visible = [False] * len(selectable)
        visible[i] = True

        region_buttons.append({
            'label': region.name,
            'method': 'update',
            'args': [
                {'visible': visible},
                {'title': f'2021 Population Density Treemap - {region.name}'}
            ]
        })

    fig.update_layout(
        title='2021 Population Density Treemap - Canada',
        updatemenus=[
            {
                'buttons': region_buttons,
                'direction': 'down',
                'showactive': True,
                'x': 0.02,
                'xanchor': 'left',
                'y': 1.06,
                'yanchor': 'top'
            }
        ],
        margin={'t': 120, 'l': 25, 'r': 25, 'b': 25}
    )

    fig.show()


def make_population_change_chart(root: RegionTree, is_percentage: bool = False) -> None:
    """
    Return a formatted value based on the is_percentage flag.

    If is_percentage is True, return the value as a percentage.
    Otherwise, return the absolute value.

    This design separates the logic at the entry point to avoid
    data loss issues caused by Plotly button toggling.
    """

    selectable = _selectable_regions(root)
    fig = go.Figure()

    title_suffix = "(Percentage Change %)" if is_percentage else "(Absolute Change)"
    y_label = "Change (%)" if is_percentage else "Change (Count)"

    for i, region in enumerate(selectable):
        children = region.subregions
        x_vals = [child.name for child in children]

        if is_percentage:
            y_vals = [child.population_change_pct(2006, 2021) for child in children]
            hover = "Change: %{y:.2f}%<extra></extra>"
        else:
            y_vals = [child.population_change(2006, 2021) for child in children]
            hover = "Change: %{y:,.0f}<extra></extra>"

        fig.add_trace(go.Bar(
            x=x_vals,
            y=y_vals,
            name=region.name,
            visible=(i == 0),
            hovertemplate=hover
        ))

    region_buttons = []
    for i, region in enumerate(selectable):
        visible_mask = [False] * len(selectable)
        visible_mask[i] = True
        region_buttons.append({
            'label': region.name,
            'method': "update",
            'args': [{"visible": visible_mask}, {"title": f"{region.name} {title_suffix}"}]
        })

    fig.update_layout(
        title=f"{selectable[0].name} {title_suffix}",
        updatemenus=[
            {
                'buttons': region_buttons,
                'direction': "down",
                'x': 0.01,
                'y': 1.08,
                'xanchor': "left"
            }
        ],
        xaxis_title="Subregions",
        yaxis_title=y_label,
        margin={'t': 100}
    )

    fig.show()


def make_population_trend_chart(root: RegionTree) -> None:
    """Display a line chart of population trend over time.

    Interface:
        - dropdown to choose a region
    """
    selectable = _selectable_regions(root)

    fig = go.Figure()

    for i, region in enumerate(selectable):
        trend = region.population_trend()

        fig.add_trace(go.Scatter(
            x=list(trend.keys()),
            y=list(trend.values()),
            mode='lines+markers',
            name=region.name,
            hovertemplate=(
                '<b>' + region.name + '</b><br>'
                'Year: %{x}<br>'
                'Population: %{y:,.0f}'
                '<extra></extra>'
            ),
            visible=(i == 0)
        ))

    region_buttons = []
    for i, region in enumerate(selectable):
        visible = [False] * len(selectable)
        visible[i] = True

        region_buttons.append({
            'label': region.name,
            'method': 'update',
            'args': [
                {'visible': visible},
                {'title': f'Population Trend - {region.name}'}
            ]
        })

    fig.update_layout(
        title='Population Trend - Canada',
        xaxis_title='Census year',
        yaxis_title='Population',
        updatemenus=[
            {
                'buttons': region_buttons,
                'direction': 'down',
                'showactive': True,
                'x': 0.02,
                'xanchor': 'left',
                'y': 1.06,
                'yanchor': 'top'
            }
        ],
        margin={'t': 110, 'l': 40, 'r': 25, 'b': 40}
    )

    fig.show()


def make_density_trend_chart(root: RegionTree) -> None:
    """Display a line chart of density trend over time.

    Interface:
        - dropdown to choose a region
    """
    selectable = _selectable_regions(root)

    fig = go.Figure()

    for i, region in enumerate(selectable):
        trend = region.density_trend()

        fig.add_trace(go.Scatter(
            x=list(trend.keys()),
            y=list(trend.values()),
            mode='lines+markers',
            name=region.name,
            hovertemplate=(
                '<b>' + region.name + '</b><br>'
                'Year: %{x}<br>'
                'Density: %{y:,.2f} people/km²'
                '<extra></extra>'
            ),
            visible=(i == 0)
        ))

    region_buttons = []
    for i, region in enumerate(selectable):
        visible = [False] * len(selectable)
        visible[i] = True

        region_buttons.append({
            'label': region.name,
            'method': 'update',
            'args': [
                {'visible': visible},
                {'title': f'Density Trend - {region.name}'}
            ]
        })

    fig.update_layout(
        title='Density Trend - Canada',
        xaxis_title='Census year',
        yaxis_title='Population density (people/km²)',
        updatemenus=[
            {
                'buttons': region_buttons,
                'direction': 'down',
                'showactive': True,
                'x': 0.02,
                'xanchor': 'left',
                'y': 1.06,
                'yanchor': 'top'
            }
        ],
        margin={'t': 110, 'l': 50, 'r': 25, 'b': 40}
    )

    fig.show()


def region_summary_text(root: RegionTree, region_name: str,
                        start_year: int = 2006,
                        end_year: int = 2021,
                        density_year: int = 2021) -> str:
    """Return a short summary text for one region."""
    region = root.find_subregion(region_name)
    if region is None:
        return f'Region "{region_name}" was not found.'

    stats = region.summary_stats(start_year, end_year, density_year)
    coverage = region.top_k_population_coverage(density_year, 5)
    variance = region.density_variance(density_year)

    lines = [
        f'Region: {stats["name"]}',
        f'Level: {stats["level"]}',
        f'Population {start_year}: {stats["population_start"]:,.0f}',
        f'Population {end_year}: {stats["population_end"]:,.0f}',
        f'Population change: {stats["population_change"]:,.0f}',
        f'Population change %: {stats["population_change_pct"]:.2f}%',
        f'Density {density_year}: {stats["density"]:,.2f} people/km²',
        f'Total area: {stats["total_area"]:,.2f} km²',
        f'Densest direct subregion: {stats["densest_subregion"]}',
        f'Fastest-growing direct subregion: {stats["fastest_growing_subregion"]}',
        f'Top 5 population coverage ({density_year}): {coverage:.2%}',
        f'Density variance ({density_year}): {variance:.2f}'
    ]
    return '\n'.join(lines)


def _build_population_change_trace(
        rows: list[dict], start_year: int, end_year: int,
        visible: bool) -> go.Treemap:
    """Return one treemap trace for a region and year interval."""
    ids = [row['id'] for row in rows]
    parents = [row['parent'] for row in rows]
    labels = [row['name'] for row in rows]
    values = [max(_get_population_from_row(row, end_year), 0.0) for row in rows]
    changes = [
        _get_population_from_row(row, end_year) - _get_population_from_row(row, start_year)
        for row in rows
    ]

    if len(changes) > 1:
        non_root_changes = changes[1:]
    else:
        non_root_changes = changes

    if non_root_changes:
        max_abs_change = max(abs(change) for change in non_root_changes)
    else:
        max_abs_change = 1.0
    if max_abs_change == 0:
        max_abs_change = 1.0

    customdata = [
        [
            row['level'],
            _get_population_from_row(row, start_year),
            _get_population_from_row(row, end_year),
            _get_population_from_row(row, end_year) - _get_population_from_row(row, start_year),
            _get_change_pct_from_row(row, start_year, end_year),
            row['land_area'],
            _get_density_from_row(row, end_year)
        ]
        for row in rows
    ]

    return go.Treemap(
        ids=ids,
        parents=parents,
        labels=labels,
        values=values,
        branchvalues='total',
        customdata=customdata,
        marker={
            'colors': changes,
            'colorscale': 'RdBu',
            'cmid': 0,
            'cmin': -max_abs_change,
            'cmax': max_abs_change,
            'colorbar': {'title': f'Change {start_year}→{end_year}'}
        },
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Level: %{customdata[0]}<br>'
            f'Population {start_year}: ' + '%{customdata[1]:,.0f}<br>'
            f'Population {end_year}: ' + '%{customdata[2]:,.0f}<br>'
            'Population change: %{customdata[3]:,.0f}<br>'
            'Population change %: %{customdata[4]:,.2f}%<br>'
            'Land area: %{customdata[5]:,.2f} km²<br>'
            f'Density {end_year}: ' + '%{customdata[6]:,.2f} people/km²'
            '<extra></extra>'
        ),
        visible=visible
    )


def _population_change_buttons(
        selectable: list[RegionTree], year_pairs: list[tuple[int, int]]) -> list[dict]:
    """Return dropdown buttons for every region and year-interval combination.

    Plotly update menus do not keep shared state across two independent menus.
    Using one combined dropdown avoids the region/year desynchronization bug.
    """
    trace_count = len(selectable) * len(year_pairs)
    buttons = []

    for region_index, region in enumerate(selectable):
        for pair_index, (start_year, end_year) in enumerate(year_pairs):
            visible = [False] * trace_count
            trace_index = region_index * len(year_pairs) + pair_index
            visible[trace_index] = True
            buttons.append({
                'label': f'{region.name} | {start_year}→{end_year}',
                'method': 'update',
                'args': [
                    {'visible': visible},
                    {
                        'title': (
                            f'Population Change Treemap - '
                            f'{region.name} ({start_year}→{end_year})'
                        )
                    }
                ]
            })

    return buttons


def make_population_change_treemap(root: RegionTree) -> None:
    """Display an interactive treemap showing population change.

    Interface:
        - one dropdown to choose both region and year interval

    Treemap settings:
        - area = population at end_year
        - color = population change from start_year to end_year

    The color scale excludes the root node from determining cmin/cmax,
    so that very large overall changes (for example Canada) do not wash
    out the colours of all other regions.
    """
    selectable = _selectable_regions(root)
    year_pairs = [
        (2006, 2011),
        (2011, 2016),
        (2016, 2021),
        (2006, 2021)
    ]

    fig = go.Figure()

    for region_index, region in enumerate(selectable):
        rows = _all_rows(region)
        for pair_index, (start_year, end_year) in enumerate(year_pairs):
            trace = _build_population_change_trace(
                rows, start_year, end_year,
                region_index == 0 and pair_index == 0
            )
            fig.add_trace(trace)

    selection_buttons = _population_change_buttons(selectable, year_pairs)

    fig.update_layout(
        title='Population Change Treemap - Canada (2006→2011)',
        updatemenus=[
            {
                'buttons': selection_buttons,
                'direction': 'down',
                'showactive': True,
                'x': 0.02,
                'xanchor': 'left',
                'y': 1.06,
                'yanchor': 'top'
            }
        ],
        margin={'t': 140, 'l': 25, 'r': 25, 'b': 25}
    )

    fig.show()


def _get_population_from_row(row: dict, year: int) -> float:
    """Return the population value for a given year from one flattened row."""
    return row[f'population_{year}']


def _get_density_from_row(row: dict, year: int) -> float:
    """Return the density value for a given year from one flattened row."""
    return row[f'density_{year}']


def _get_change_pct_from_row(row: dict, start_year: int, end_year: int) -> float:
    """Return the percentage population change between two years from one row."""
    start_pop = row[f'population_{start_year}']
    end_pop = row[f'population_{end_year}']
    if start_pop == 0:
        return 0.0
    return ((end_pop - start_pop) / start_pop) * 100


def make_top_dense_chart(root: RegionTree) -> None:
    """Top 10 most dense subdivisions (2021)."""

    regions = root.top_k_dense_subregions(2021, 'subdivision', 10)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[r.name for r in regions],
        y=[r.density(2021) for r in regions],
        hovertemplate=(
            '<b>%{x}</b><br>'
            'Density: %{y:,.2f} people/km²'
            '<extra></extra>'
        )
    ))

    fig.update_layout(
        title='Top 10 Most Dense Regions (2021)',
        xaxis_title='Region',
        yaxis_title='Density',
        margin={'t': 100}
    )

    fig.show()


def make_top_growth_chart(root: RegionTree) -> None:
    """Top 10 fastest-growing subdivisions (2006–2021)."""

    regions = root.top_k_growing_subregions(2006, 2021, 'subdivision', 10)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[r.name for r in regions],
        y=[r.population_change(2006, 2021) for r in regions],
        hovertemplate=(
            '<b>%{x}</b><br>'
            'Population change: %{y:,.0f}'
            '<extra></extra>'
        )
    ))

    fig.update_layout(
        title='Top 10 Fastest Growing Regions (2006–2021)',
        xaxis_title='Region',
        yaxis_title='Population Growth',
        margin={'t': 100}
    )

    fig.show()


def show_yearly_changes(root: RegionTree) -> None:
    """Show year-to-year population changes as a bar chart."""

    changes = root.year_to_year_changes()

    periods = list(changes.keys())
    values = list(changes.values())

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=periods,
        y=values,
        hovertemplate=(
            '<b>%{x}</b><br>'
            'Population change: %{y:,.0f}'
            '<extra></extra>'
        )
    ))

    fig.update_layout(
        title='Population Change by Period (Canada)',
        xaxis_title='Period',
        yaxis_title='Population Change',
        margin={'t': 100}
    )

    fig.show()


def make_high_density_chart(root: RegionTree) -> None:
    """Show high-density cities as a bar chart."""

    threshold = 1000

    cities = root.find_high_density_cities(threshold, 2021)[:10]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[c.name for c in cities],
        y=[c.density(2021) for c in cities],
        hovertemplate=(
            '<b>%{x}</b><br>'
            'Density: %{y:,.2f}'
            '<extra></extra>'
        )
    ))

    fig.update_layout(
        title=f'Cities with Density > {threshold} (Top 10)',
        xaxis_title='City',
        yaxis_title='Density',
        margin={'t': 100}
    )

    fig.show()


def _historical_population_series(root: RegionTree) -> tuple[list[int], list[float]]:
    """Return historical census years and corresponding populations."""
    years = [2006, 2011, 2016, 2021]
    populations = [root.total_population(year) for year in years]
    return years, populations


def _prediction_model_values(years: list[int], populations: list[float]) -> PredictionModel:
    """Return regression and prediction values for the prediction chart."""
    n = len(years)
    mean_x = sum(years) / n
    mean_y = sum(populations) / n

    numerator = sum((years[i] - mean_x) * (populations[i] - mean_y) for i in range(n))
    denominator = sum((years[i] - mean_x) ** 2 for i in range(n))
    slope = numerator / denominator
    intercept = mean_y - slope * mean_x

    predicted_2026 = max(0.0, slope * 2026 + intercept)
    extended_years = [2006, 2011, 2016, 2021, 2026]
    fitted_values = [max(0.0, slope * year + intercept) for year in extended_years]

    errors = [populations[i] - (slope * years[i] + intercept) for i in range(n)]
    mse = sum(error ** 2 for error in errors) / n
    std_error = mse ** 0.5

    return {
        'slope': slope,
        'intercept': intercept,
        'predicted_2026': predicted_2026,
        'extended_years': extended_years,
        'fitted_values': fitted_values,
        'upper': predicted_2026 + std_error,
        'lower': max(0.0, predicted_2026 - std_error)
    }


def _add_traces_for_region(fig: go.Figure, region: RegionTree, visible: bool) -> None:
    """Add all prediction traces for one region to fig."""
    years, populations = _historical_population_series(region)
    model = _prediction_model_values(years, populations)

    fig.add_trace(go.Scatter(
        x=years,
        y=populations,
        mode='markers+lines',
        name='Actual Data',
        hovertemplate=(
            '<b>' + region.name + '</b><br>'
            'Year: %{x}<br>'
            'Population: %{y:,.0f}'
            '<extra></extra>'
        ),
        visible=visible
    ))

    fig.add_trace(go.Scatter(
        x=model['extended_years'],
        y=model['fitted_values'],
        mode='lines',
        name='Regression Line',
        hovertemplate=(
            '<b>' + region.name + '</b><br>'
            'Year: %{x}<br>'
            'Fitted population: %{y:,.0f}'
            '<extra></extra>'
        ),
        visible=visible
    ))

    fig.add_trace(go.Scatter(
        x=[2026],
        y=[model['predicted_2026']],
        mode='markers',
        name='2026 linear baseline',
        marker={'size': 12, 'symbol': 'diamond'},
        hovertemplate=(
            '<b>' + region.name + '</b><br>'
            '2026 linear baseline: %{y:,.0f}'
            '<extra></extra>'
        ),
        visible=visible
    ))

    fig.add_trace(go.Scatter(
        x=[2026, 2026],
        y=[model['lower'], model['upper']],
        mode='lines',
        name='Historical fit dispersion',
        line={'width': 6},
        hovertemplate=(
            '<b>' + region.name + '</b><br>'
            'Historical fit dispersion: %{y:,.0f}'
            '<extra></extra>'
        ),
        visible=visible
    ))


def make_population_prediction(root: RegionTree) -> None:
    """Show population prediction for Canada and each province/territory."""
    selectable = _selectable_regions(root)
    fig = go.Figure()
    traces_per_region = 4

    for i, region in enumerate(selectable):
        _add_traces_for_region(fig, region, i == 0)

    buttons = []
    for i, region in enumerate(selectable):
        visible = [False] * (len(selectable) * traces_per_region)
        start = i * traces_per_region

        for j in range(traces_per_region):
            visible[start + j] = True

        model = _prediction_model_values(*_historical_population_series(region))

        buttons.append({
            'label': region.name,
            'method': 'update',
            'args': [
                {'visible': visible},
                {
                    'title': f'Population Prediction using Linear Regression - {region.name}',
                    'annotations': [{
                        'x': 0.5,
                        'y': 1.12,
                        'xref': 'paper',
                        'yref': 'paper',
                        'showarrow': False,
                        'text': (
                            f"y = {model['slope']:.2f}x + {model['intercept']:.0f}<br>"
                            f"2026 linear baseline: {model['predicted_2026']:,.0f}<br>"
                            'Band shows historical fit dispersion; it is not a confidence interval.'
                        )
                    }]
                }
            ]
        })

    canada_model = _prediction_model_values(*_historical_population_series(root))

    fig.update_layout(
        title='Population Prediction using Linear Regression - Canada',
        xaxis_title='Year',
        yaxis_title='Population',
        updatemenus=[
            {
                'buttons': buttons,
                'direction': 'down',
                'showactive': True,
                'x': 0.02,
                'xanchor': 'left',
                'y': 1.12,
                'yanchor': 'top'
            }
        ],
        annotations=[{
            'x': 0.5,
            'y': 1.12,
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'text': (
                f"y = {canada_model['slope']:.2f}x + {canada_model['intercept']:.0f}<br>"
                f"2026 linear baseline: {canada_model['predicted_2026']:,.0f}<br>"
                'Band shows historical fit dispersion; it is not a confidence interval.'
            )
        }],
        margin={'t': 140, 'l': 50, 'r': 25, 'b': 40},
        template='plotly_white'
    )

    fig.show()


def make_prediction_chart(root: RegionTree) -> None:
    """Show the population prediction chart."""
    make_population_prediction(root)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
