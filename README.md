# Blend-Mix-Optimizer-2

Ore blend mix optimization system for the BF-02 blast furnace bunker. This Streamlit application helps process engineers design ore blends that meet chemistry constraints while controlling slag and cost.

## Features

- **Interactive ore catalogue**: View FY 2025–26 average chemistry for all bunker ores and materials.
- **LP-based optimal blend**: Linear programming optimizer to find a feasible, cost- and chemistry-efficient blend given:
  - Selected ores and maximum available quantities
  - Target blend quantity
  - Ore prices
  - Optimization goal (e.g. minimize cost, meet Fe% / slag constraints)
- **Overflow resolver**: Automatically adjusts recommended quantities when the LP solution exceeds bunker limits, respecting a user-defined priority list.
- **Grid search around optimum**: Explores nearby blends around the LP optimum to build a Pareto front of cost vs. chemistry/slag.
- **Rich visualization dashboard**:
  - Pareto scatter of all valid blends
  - Fe contribution waterfall by ore
  - Composition bar charts for top blends
  - Radar comparison of multiple candidate blends

## Project structure

```text
app.py                 # Main Streamlit entry point
data/
  ore_chemistry.py     # Loads and preprocesses ore chemistry data
engine/
  blend_calculator.py  # Blend chemistry and KPI calculations
  optimizer.py         # LP optimizer for optimal blend
  overflow_resolver.py # Resolves bunker overflows with priorities
  grid_search.py       # Local grid search around optimum
ui/
  sidebar.py           # Sidebar controls and input collection
  results.py           # Best blend card and tables
  charts.py            # Plotly charts and visualizations
assests/
  BF02_Ores_Chemical_Composition.xlsx  # Source ore chemistry input
```

## Requirements

- **Python**: >= 3.11
- **Core libraries** (also listed in `pyproject.toml` / `requirements.txt`):
  - `streamlit`
  - `pandas`
  - `numpy`
  - `scipy`
  - `plotly`
  - `openpyxl`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # On Windows
pip install -r requirements.txt
```

If you prefer `uv` or another manager, ensure the dependencies from `pyproject.toml` are installed into your environment.

## Running the app

From the project root:

```bash
streamlit run app.py
```

This launches the BF-02 Ore Blend Optimizer in your browser. Use the sidebar to:

- Select ores/materials for the blend
- Enter maximum quantities and prices
- Choose the optimization goal and step size
- Run the optimizer and inspect optimal and alternative blends

## Data and customization

- **Chemistry source**: The default ore chemistry comes from `assests/BF02_Ores_Chemical_Composition.xlsx`, loaded via `data/ore_chemistry.py`.
- **Updating chemistry**: To use different periods or furnaces, update the Excel file (column names and structure should remain consistent) or adjust `ore_chemistry.py` accordingly.
- **Business rules**: Any furnace-specific constraints, priorities, or KPIs can be extended in the `engine/` modules and reflected in the `ui/` components.
