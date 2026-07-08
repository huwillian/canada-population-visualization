"""Run the full Canada population visualization program.

This module is the main entry point and coordinator for the entire project.
Its role is not to clean raw data, define the tree structure, or implement
individual charts. Instead, it connects all of those parts together and
provides the user-facing interface for launching the program.

The overall code idea in this file is orchestration. It takes the cleaned
dataset produced earlier, passes it into the loader to build a RegionTree,
updates the internal aggregate values of that tree, and then opens a menu
through which the user can choose different analyses and visualizations.

The main function performs the high-level startup workflow of the project:
- load the cleaned population CSV
- build the RegionTree structure
- update aggregate population and land-area values for internal nodes
- print a few example region summaries to show that the data structure is
  working correctly
- launch the interactive menu window

The launch_menu function is responsible for the graphical interface. It builds
a scrollable Tkinter window that acts as a simple control panel for the whole
project. Rather than displaying every chart at once, the menu presents the user
with a list of buttons. Each button opens one visualization or analysis page.

This design has two important advantages.

First, it keeps the project organized. The visualization code remains inside
the visualization module, and the tree logic remains inside the RegionTree
module. This file simply coordinates them.

Second, it improves usability. Because the project contains many charts and
analysis tools, a menu-based interface makes it easier for the user to explore
the project one feature at a time instead of being overwhelmed by all outputs
at once.

For these reasons, this file acts as the controller of the project. It is the
place where separate components become one complete application that a user can
run, navigate, and demonstrate.
"""
import tkinter as tk

from data_loader import build_tree_from_csv
from visualization import (
    make_density_treemap,
    make_population_change_treemap,
    make_population_change_chart,
    make_population_trend_chart,
    make_density_trend_chart,
    region_summary_text,
    make_top_dense_chart,
    make_top_growth_chart,
    show_yearly_changes,
    make_high_density_chart,
    make_prediction_chart
)


def launch_menu(root_data: object) -> None:
    """Open a scrollable interface window so the user can choose one page."""
    window = tk.Tk()
    window.title('Canada Population Visualization')
    window.geometry('500x700')
    window.minsize(420, 500)

    # Main container
    container = tk.Frame(window)
    container.pack(fill='both', expand=True)

    # Canvas + scrollbar
    canvas = tk.Canvas(container)
    scrollbar = tk.Scrollbar(container, orient='vertical', command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        '<Configure>',
        lambda event: canvas.configure(scrollregion=canvas.bbox('all'))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    # Optional: mouse wheel scrolling
    def _on_mousewheel(event: tk.Event) -> None:
        canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    canvas.bind_all('<MouseWheel>', _on_mousewheel)

    # ----- Content -----
    title = tk.Label(
        scrollable_frame,
        text='Choose a visualization',
        font=('Arial', 16, 'bold')
    )
    title.pack(pady=(15, 10))

    subtitle = tk.Label(
        scrollable_frame,
        text='Click one button to open the original page.',
        font=('Arial', 11)
    )
    subtitle.pack(pady=(0, 15))

    tk.Label(
        scrollable_frame,
        text='Visualization',
        font=('Arial', 13, 'bold')
    ).pack(pady=(10, 5))

    tk.Button(
        scrollable_frame,
        text='1. Density Treemap',
        width=30,
        command=lambda: make_density_treemap(root_data)
    ).pack(pady=5)

    tk.Button(
        scrollable_frame,
        text='2. Population Change Treemap',
        width=30,
        command=lambda: make_population_change_treemap(root_data)
    ).pack(pady=5)

    tk.Label(
        scrollable_frame,
        text='Analysis',
        font=('Arial', 13, 'bold')
    ).pack(pady=(15, 5))

    tk.Button(
        scrollable_frame,
        text='3a. Pop Change (Absolute)',
        width=30,
        command=lambda: make_population_change_chart(root_data, is_percentage=False)
    ).pack(pady=5)

    tk.Button(
        scrollable_frame,
        text='3b. Pop Change (Percentage)',
        width=30,
        command=lambda: make_population_change_chart(root_data, is_percentage=True)
    ).pack(pady=5)

    tk.Button(
        scrollable_frame,
        text='4. Population Trend Chart',
        width=30,
        command=lambda: make_population_trend_chart(root_data)
    ).pack(pady=5)

    tk.Button(
        scrollable_frame,
        text='5. Density Trend Chart',
        width=30,
        command=lambda: make_density_trend_chart(root_data)
    ).pack(pady=5)

    tk.Button(
        scrollable_frame,
        text='6. Top Dense Regions',
        width=30,
        command=lambda: make_top_dense_chart(root_data)
    ).pack(pady=5)

    tk.Button(
        scrollable_frame,
        text='7. Top Growing Regions',
        width=30,
        command=lambda: make_top_growth_chart(root_data)
    ).pack(pady=5)

    tk.Button(
        scrollable_frame,
        text='8. High Density Filter',
        width=30,
        command=lambda: make_high_density_chart(root_data)
    ).pack(pady=5)

    tk.Button(
        scrollable_frame,
        text='9. Yearly Changes',
        width=30,
        command=lambda: show_yearly_changes(root_data)
    ).pack(pady=5)

    tk.Button(
        scrollable_frame,
        text='10. Population Prediction (2026)',
        width=30,
        command=lambda: make_prediction_chart(root_data)
    ).pack(pady=5)

    tk.Button(
        scrollable_frame,
        text='Close',
        width=20,
        command=window.destroy
    ).pack(pady=(20, 20))

    window.mainloop()


def main() -> None:
    """Run the project visualizations."""
    root = build_tree_from_csv('cleaned_population_2006_2021_augmented.csv')
    root.update_aggregates()
    print(region_summary_text(root, 'Canada'))
    print()
    print(region_summary_text(root, 'Ontario'))
    launch_menu(root)


if __name__ == '__main__':
    import python_ta
    main()
    python_ta.check_all(config={
        'extra-imports': ['data_loader', 'visualization', 'tkinter', 'python_ta'],
        'allowed-io': ['main'],
        'max-line-length': 100
    })
