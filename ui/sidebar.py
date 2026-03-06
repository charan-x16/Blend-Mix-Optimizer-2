"""
UI Sidebar — Ore selection, quantity inputs, price inputs, fuel inputs.

Flow:
  Step 1        — Ore checkboxes (outside form)
  Steps 2-5     — Numeric inputs + fuel inside st.sidebar.form
  Submit        — Validates and saves to session state
  Step 6        — Grid search step size (outside form)
  Run Optimizer — Uses session state values to run
"""

import streamlit as st
import pandas as pd
from data.ore_chemistry import get_ore_flag
from config.config import cfg
from engine.fuel_calculator import FuelInput

INPUTS_KEY = "submitted_inputs"
READY_KEY  = "optimizer_ready"


def render_sidebar(chemistry_df: pd.DataFrame) -> dict | None:
    st.sidebar.title("Blend Configuration")

    all_ores = chemistry_df.index.tolist()

    # ── Step 1: Select Ores (outside form) ───────────────────────────────────
    st.sidebar.subheader("Step 1 — Select Ores")
    st.sidebar.caption("Choose ores available in the yard today")

    selected_ores = []
    for ore in all_ores:
        flag  = get_ore_flag(ore)
        label = f"{ore}  {flag}" if flag else ore
        if st.sidebar.checkbox(label, value=False, key=f"ore_check_{ore}"):
            selected_ores.append(ore)

    if len(selected_ores) < 2:
        st.sidebar.warning("Select at least 2 ores to begin.")
        st.session_state.pop(INPUTS_KEY, None)
        st.session_state.pop(READY_KEY, None)
        return None

    st.sidebar.divider()

    # ── Steps 2–5 + Submit inside form ───────────────────────────────────────
    with st.sidebar.form(key="blend_config_form"):

        # ── Step 2: Target Blend Quantity ─────────────────────────────────────
        st.subheader("Step 2 — Target Blend")
        target_qty = st.number_input(
            "Total Target Blend (MT)",
            min_value=10.0,
            max_value=50000.0,
            value=cfg.default_target_qty,
            step=50.0,
            help="Total tonnes of ore blend required",
        )

        st.divider()

        # ── Step 3: Available Quantities ──────────────────────────────────────
        st.subheader("Step 3 — Available Quantities (MT)")
        st.caption("Enter max available tonnes per ore")

        max_quantities = {}
        for ore in selected_ores:
            qty = st.number_input(
                ore,
                min_value=1.0,
                max_value=99999.0,
                value=float(target_qty),
                step=10.0,
                key=f"qty_{ore}",
            )
            max_quantities[ore] = qty

        st.divider()

        # ── Step 4: Prices ─────────────────────────────────────────────────────
        st.subheader("Step 4 — Price per MT (₹)")
        st.caption("Enter current purchase price per tonne")

        prices = {}
        for ore in selected_ores:
            price = st.number_input(
                ore,
                min_value=0.0,
                max_value=99999.0,
                value=cfg.ore_prices.get(ore, cfg.fallback_price),
                step=100.0,
                key=f"price_{ore}",
            )
            prices[ore] = price

        st.divider()

        # ── Step 5: Fuel Inputs ───────────────────────────────────────────────
        st.subheader("Step 5 — Fuel (Coke / Nut Coke / PCI)")
        st.caption("Slag contribution auto-calculated from ash analysis in config")

        st.markdown("**🔥 Coke**")
        coke_qty = st.number_input(
            "Coke Quantity (MT)",
            min_value=0.0, max_value=9999.0,
            value=cfg.coke_defaults["qty_mt"], step=10.0,
            key="coke_qty",
        )
        coke_ash = st.number_input(
            "Coke Ash%",
            min_value=0.0, max_value=50.0,
            value=cfg.coke_defaults["ash_pct"], step=0.1,
            key="coke_ash",
        )

        st.markdown("**🔥 Nut Coke**")
        nut_coke_qty = st.number_input(
            "Nut Coke Quantity (MT)",
            min_value=0.0, max_value=9999.0,
            value=cfg.nut_coke_defaults["qty_mt"], step=10.0,
            key="nut_coke_qty",
        )
        nut_coke_ash = st.number_input(
            "Nut Coke Ash%",
            min_value=0.0, max_value=50.0,
            value=cfg.nut_coke_defaults["ash_pct"], step=0.1,
            key="nut_coke_ash",
        )

        st.markdown("**🔥 PCI**")
        pci_qty = st.number_input(
            "PCI Quantity (MT)",
            min_value=0.0, max_value=9999.0,
            value=cfg.pci_defaults["qty_mt"], step=10.0,
            key="pci_qty",
        )
        pci_ash = st.number_input(
            "PCI Ash%",
            min_value=0.0, max_value=50.0,
            value=cfg.pci_defaults["ash_pct"], step=0.1,
            key="pci_ash",
        )

        st.divider()

        # ── Submit Button ──────────────────────────────────────────────────────
        submitted = st.form_submit_button(
            "Submit",
            use_container_width=True,
        )

    # ── Validate and save on submit ───────────────────────────────────────────
    if submitted:
        total_available = sum(max_quantities.values())
        if total_available < target_qty:
            st.sidebar.error(
                f"Total available ({total_available:.0f} MT) is less than "
                f"target ({target_qty:.0f} MT). Fix before submitting."
            )
            st.session_state.pop(INPUTS_KEY, None)
        else:
            fuel_input = FuelInput(
                coke_qty_mt=coke_qty,         coke_ash_pct=coke_ash,
                nut_coke_qty_mt=nut_coke_qty, nut_coke_ash_pct=nut_coke_ash,
                pci_qty_mt=pci_qty,           pci_ash_pct=pci_ash,
            )
            st.session_state[INPUTS_KEY] = {
                "selected_ores":  selected_ores,
                "max_quantities": max_quantities,
                "prices":         prices,
                "target_qty":     target_qty,
                "fuel_input":     fuel_input,
            }
            st.session_state.pop(READY_KEY, None)
            st.sidebar.success("✅ Inputs saved. Select step size and run.")

    # Show saved inputs summary
    if INPUTS_KEY in st.session_state:
        saved = st.session_state[INPUTS_KEY]
        with st.sidebar.expander("📋 Saved inputs", expanded=False):
            st.write(f"**Target:** {saved['target_qty']:.0f} MT")
            st.write(f"**Ores:** {', '.join(saved['selected_ores'])}")
            for ore in saved['selected_ores']:
                st.write(f"  • {ore}: {saved['max_quantities'][ore]:.0f} MT @ ₹{saved['prices'][ore]:,.0f}")
            fi = saved["fuel_input"]
            st.write(f"**Coke:** {fi.coke_qty_mt:.0f} MT, Ash {fi.coke_ash_pct}%")
            st.write(f"**Nut Coke:** {fi.nut_coke_qty_mt:.0f} MT, Ash {fi.nut_coke_ash_pct}%")
            st.write(f"**PCI:** {fi.pci_qty_mt:.0f} MT, Ash {fi.pci_ash_pct}%")

    st.sidebar.divider()

    # ── Step 6: Grid Search Step Size (outside form) ──────────────────────────
    st.sidebar.subheader("Step 6 — Grid Search Step Size")
    step_size = st.sidebar.select_slider(
        "Step Size (MT)",
        options=[5, 10, 25, 50, 100],
        value=10,
        help="Smaller steps = more candidate blends = slightly slower",
    )

    st.sidebar.divider()

    # ── Run Optimizer Button ──────────────────────────────────────────────────
    if INPUTS_KEY not in st.session_state:
        st.sidebar.info("Complete all steps and click Submit first.")
        return None

    if st.sidebar.button("Run Optimizer", type="primary", use_container_width=True):
        st.session_state[READY_KEY] = True

    if not st.session_state.get(READY_KEY, False):
        return None

    return {
        **st.session_state[INPUTS_KEY],
        "step_size": float(step_size),
    }