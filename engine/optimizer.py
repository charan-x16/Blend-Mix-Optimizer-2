"""
LP Optimizer — Finds the single optimal blend using linear programming.
Uses scipy.optimize.linprog to solve the blend problem.

Objectives:
  - Minimize Cost:  minimize Σ(x_i × price_i)
  - Maximize Fe%:   minimize -Σ(x_i × Fe_i) / total  →  minimize -Σ(x_i × Fe_i)
  - Minimize Slag%: minimize Σ(x_i × Slag_i) / total  →  minimize Σ(x_i × Slag_i)

Constraints:
  Σ x_i = target_qty         (equality)
  x_i ≥ P25% × target_qty    (lower bound — scales with target)
  x_i ≤ max_qty_i            (upper bound = availability)
"""

import numpy as np
from scipy.optimize import linprog
import pandas as pd
from engine.blend_calculator import calculate_blend, BlendResult

# ── P25 Minimum Feasible Percentages (% of total blend) ──────────────────────
# Derived from BF-02 DPR actuals (Sep'24 → Mar'26).
# P25 = 25th percentile of (daily ore usage / daily total IBRM) × 100
# when ore was actively used.
#
# These are percentages, NOT absolute MT values.
# At runtime:  min_qty_i = (ORE_MIN_PCT[ore] / 100) × target_qty
#
# This makes the constraint scale-independent:
#   - 3000 MT target → Sinter min = 1950 MT (65%)
#   - 8000 MT target → Sinter min = 5200 MT (65%)
# ──────────────────────────────────────────────────────────────────────────────
# ORE_MIN_PCT = {
#     "NMDC ROM":               9.65,
#     "NMDC Donimalai":         1.02,
#     "Bacheli Fines O/S":      3.55,
#     "Lloyds Pellet (Sarda)":  0.25,
#     "Lloyds Fines O/S":       7.22,
#     "Lloyds CLO":            15.74,
#     "JRS Ventures CLO":       3.41,
#     "Jayaswal Neco":          0.83,
#     "Gomti CLO":              8.18,
#     "Titani Ferrous CLO":     0.59,
#     "Geomin CLO":             9.02,
#     "Acore MN Ore":           0.77,
#     "NMDC Kirandul CLO":      2.26,
#     "Sinter (SP-02)":        65.01,
# }

ORE_MIN_PCT = {
    "NMDC ROM":               0,
    "NMDC Donimalai":         0,
    "Bacheli Fines O/S":      0,
    "Lloyds Pellet (Sarda)":  0,
    "Lloyds Fines O/S":       0,
    "Lloyds CLO":             0,
    "JRS Ventures CLO":       0,
    "Jayaswal Neco":          0,
    "Gomti CLO":              0,
    "Titani Ferrous CLO":     0,
    "Geomin CLO":             0,
    "Acore MN Ore":           0,
    "NMDC Kirandul CLO":      0,
    # "Sinter (SP-02)":        60,
}

SINTER_MAX_PCT = 0.70
SINTER_MIN_PCT = 0.50

FALLBACK_MIN_PCT = 0.5  # default 0.5% if ore name not found in lookup


def _get_min_qty(ore_name: str, target_qty: float) -> float:
    """
    Return the P25-based minimum MT for a given ore and target quantity.
    min_qty = (P25_pct / 100) × target_qty
    """
    pct = ORE_MIN_PCT.get(ore_name, FALLBACK_MIN_PCT)
    return round((pct / 100.0) * target_qty, 1)


def run_optimizer(
    selected_ores: list[str],
    max_quantities: dict,       # {ore_name: max_MT}
    prices: dict,               # {ore_name: ₹/MT}
    target_qty: float,
    goal: str,                  # "Minimize Cost" | "Maximize Fe%" | "Minimize Slag%"
    chemistry_df: pd.DataFrame,
) -> BlendResult | None:
    """
    Run LP optimizer and return the optimal BlendResult, or None if infeasible.
    """
    n = len(selected_ores)
    idx = {ore: i for i, ore in enumerate(selected_ores)}

    # ── Objective vector ──────────────────────────────────────────────────────
    if goal == "Minimize Cost":
        c = np.array([prices.get(ore, 0) for ore in selected_ores], dtype=float)

    elif goal == "Maximize Fe%":
        c = np.array(
            [-float(chemistry_df.loc[ore, "%Fe(T)"]) for ore in selected_ores],
            dtype=float,
        )

    elif goal == "Minimize Slag%":
        slag_vals = []
        for ore in selected_ores:
            slag = sum(
                float(chemistry_df.loc[ore, col])
                for col in ["%SiO2", "%Al2O3", "%CaO", "%MgO", "%MnO"]
                if col in chemistry_df.columns
            )
            slag_vals.append(slag * 0.01)
        c = np.array(slag_vals, dtype=float)
    else:
        raise ValueError(f"Unknown goal: {goal}")

    # ── Equality constraint: Σ x_i = target_qty ──────────────────────────────
    A_eq = np.ones((1, n))
    b_eq = np.array([target_qty])
    
    slag_vals = []
    for ore in selected_ores:
        slag = sum(
            float(chemistry_df.loc[ore, col])
            for col in ["%SiO2", "%Al2O3", "%CaO", "%MgO", "%MnO"]
            if col in chemistry_df.columns
        )
        slag_vals.append(slag * 0.01)


    target_slag_qty = 700 # in Tonnes of hotmetal

    A_ub = np.array([slag_vals]).reshape((1,-1))
    b_ub = np.array([target_slag_qty])

    # ── Bounds: P25_min ≤ x_i ≤ max_qty_i ────────────────────────────────────
    # Uses operationally practical minimums derived from BF-02 DPR data.
    # Scales with target quantity so it works for any blend size.
    bounds = []
    for ore in selected_ores:
        # lo = _get_min_qty(ore, target_qty)
        if "sinter" in ore.lower():
            hi = SINTER_MAX_PCT * target_qty
            lo = SINTER_MIN_PCT * target_qty
        else:
            hi = max_quantities.get(ore, target_qty)
            lo = _get_min_qty(ore, target_qty)

        bounds.append((lo, hi))

    # ── Solve ─────────────────────────────────────────────────────────────────
    result = linprog(
        c,
        A_eq=A_eq,
        b_eq=b_eq,
        A_ub = A_ub,
        b_ub = b_ub,
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        return None

    # Round to 1 decimal, but respect the P25 floor
    quantities = {}
    for i, ore in enumerate(selected_ores):
        lo = bounds[i][0]
        qty = max(lo, round(result.x[i], 1))
        quantities[ore] = qty

    return calculate_blend(quantities, prices, chemistry_df)