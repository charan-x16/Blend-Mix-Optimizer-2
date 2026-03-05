"""
UI Sidebar — Ore selection, quantity inputs, price inputs, goal selection.
Returns all operator inputs as structured dicts.

Changes from v1:
  - Added "Balanced Optimization" as 4th goal option
  - Removed Vendor Priority (Step 6) — not intuitive for operators
  - Steps renumbered: 1 Select, 2 Target, 3 Quantities, 4 Prices, 5 Goal, 6 Step Size
"""

import streamlit as st
import pandas as pd
from data.ore_chemistry import get_ore_flag


def render_sidebar(chemistry_df: pd.DataFrame) -> dict | None:
    """
    Render the full sidebar UI.
    Returns dict of operator inputs, or None if not ready to run.
    """
    st.sidebar.markdown("""
    <div style='padding: 0.5rem 0 1rem 0;'>
        <h2 style='font-family: monospace; font-size: 1.1rem;
                   color: #E8A020; margin: 0; letter-spacing: 2px;'>
            ⚙️ BLEND CONFIGURATION
        </h2>
    </div>
    """, unsafe_allow_html=True)

    all_ores = chemistry_df.index.tolist()

    # ── Step 1: Select Ores ───────────────────────────────────────────────────
    st.sidebar.markdown("### Step 1 — Select Ores")
    st.sidebar.caption("Choose ores available in the yard today")

    selected_ores = []
    for ore in all_ores:
        flag = get_ore_flag(ore)
        label = f"{ore}  {flag}" if flag else ore
        if st.sidebar.checkbox(label, value=False, key=f"ore_check_{ore}"):
            selected_ores.append(ore)

    if len(selected_ores) < 2:
        st.sidebar.warning("Select at least 2 ores to begin.")
        return None

    st.sidebar.divider()

    # ── Step 2: Target Blend Quantity ─────────────────────────────────────────
    st.sidebar.markdown("### Step 2 — Target Blend")
    target_qty = st.sidebar.number_input(
        "Total Target Blend (MT)",
        min_value=10.0,
        max_value=50000.0,
        value=3800.0,
        step=50.0,
        help="Total tonnes of ore blend required",
    )

    st.sidebar.divider()

    # ── Step 3: Available Quantities ──────────────────────────────────────────
    st.sidebar.markdown("### Step 3 — Available Quantities (MT)")
    st.sidebar.caption("Enter max available tonnes per ore")

    max_quantities = {}
    total_available = 0.0
    for ore in selected_ores:
        qty = st.sidebar.number_input(
            ore,
            min_value=1.0,
            max_value=99999.0,
            value=float(1*target_qty),
            step=10.0,
            key=f"qty_{ore}",
        )
        max_quantities[ore] = qty
        total_available += qty

    if total_available < target_qty:
        st.sidebar.error(
            f"⚠️ Total available ({total_available:.0f} MT) < "
            f"Target ({target_qty:.0f} MT). Add more ore or reduce target."
        )
        return None

    st.sidebar.divider()

    # ── Step 4: Prices ────────────────────────────────────────────────────────
    st.sidebar.markdown("### Step 4 — Price per MT (₹)")
    st.sidebar.caption("Enter current purchase price per tonne")

    ore_price_dict = {
        "NMDC ROM":               8739.0,
        "NMDC Donimalai":         5684.0,
        "Bacheli Fines O/S":      10000.0,
        "Lloyds Pellet (Sarda)":  9650.0,
        "Lloyds Fines O/S":       6162.0,
        "Lloyds CLO":             8051.0,
        "JRS Ventures CLO":       6831.0,
        "Jayaswal Neco":          6650.0,
        "Gomti CLO":              5349.0,
        "Titani Ferrous CLO":     4939.0,
        "Geomin CLO":             3827.0,
        "Acore MN Ore":           8473.0,
        "NMDC Kirandul CLO":      10000.0,
        "Sinter (SP-02)":         5282.0,
    }
    
    prices = {}
    for ore in selected_ores:
        price = st.sidebar.number_input(
            ore,
            min_value=0.0,
            max_value=99999.0,
            value=ore_price_dict[ore],
            step=100.0,
            key=f"price_{ore}",
        )
        prices[ore] = price

    st.sidebar.divider()

    # ── Step 5: Optimization Goal ─────────────────────────────────────────────
    st.sidebar.markdown("### Step 5 — Optimization Goal")

    goal = st.sidebar.radio(
        "What matters most today?",
        options=[
            "Minimize Cost",
            "Maximize Fe%",
            "Minimize Slag%",
            "Balanced Optimization",
        ],
        index=0,
        help=(
            "Minimize Cost: cheapest blend that hits target.\n"
            "Maximize Fe%: highest iron grade blend.\n"
            "Minimize Slag%: lowest slag burden blend.\n"
            "Balanced: finds blends that perform well across all three goals simultaneously."
        ),
    )

    # Explain balanced mode inline
    if goal == "Balanced Optimization":
        st.sidebar.info(
            "⚖️ Balanced mode runs all three optimizations, "
            "identifies blends that appear in all result sets, "
            "and ranks them by a combined cost + Fe + slag score."
        )

    st.sidebar.divider()

    # ── Step 6: Grid Search Step Size ────────────────────────────────────────
    st.sidebar.markdown("### Step 6 — Grid Search Settings")
    step_size = st.sidebar.select_slider(
        "Step Size (MT)",
        options=[5, 10, 25, 50, 100],
        value=10,
        help="Smaller steps = more candidate blends = slightly slower",
    )

    st.sidebar.divider()

    # ── Run Button ────────────────────────────────────────────────────────────
    run = st.sidebar.button(
        "🚀 RUN OPTIMIZER",
        type="primary",
        width='stretch',
    )

    if not run:
        return None

    return {
        "selected_ores":  selected_ores,
        "max_quantities": max_quantities,
        "prices":         prices,
        "target_qty":     target_qty,
        "goal":           goal,
        "step_size":      float(step_size),
    }