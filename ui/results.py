"""
UI Results — Best blend card, balanced results display, and top blends table.
"""

import streamlit as st
import pandas as pd
from engine.blend_calculator import BlendResult


# ── Single-goal optimal blend card ───────────────────────────────────────────

def render_best_blend_card(result: BlendResult, goal: str):
    """Render a single optimal blend card."""
    GOAL_ICONS = {
        "Minimize Cost":  ("💰", "#4FC3F7"),
        "Maximize Fe%":   ("⬆️ Fe", "#81C784"),
        "Minimize Slag%": ("⬇️ Slag", "#CE93D8"),
    }
    icon, color = GOAL_ICONS.get(goal, ("★", "#E8A020"))

    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border: 1px solid {color};
                border-radius: 12px;
                padding: 1.2rem 1.5rem;
                margin-bottom: 1rem;'>
        <span style='color: {color}; font-family: monospace;
                     font-size: 0.85rem; letter-spacing: 2px;'>
            {icon} &nbsp; {goal.upper()}
        </span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Fe%", f"{result.fe_pct:.2f}%")
    with col2:
        st.metric("Slag%", f"{result.slag_pct:.2f}%")
    with col3:
        st.metric("Slag MT", f"{result.slag_mt:.1f}")
    with col4:
        st.metric("Cost/MT", f"₹{result.cost_per_mt:,.0f}")
    with col5:
        st.metric("Total Cost", f"₹{result.total_cost/100000:.2f}L")

    with st.expander("🔬 Full chemistry + composition", expanded=False):
        qty_cols = st.columns(len(result.quantities))
        for i, (ore, qty) in enumerate(result.quantities.items()):
            pct = (qty / result.total_qty) * 100
            with qty_cols[i]:
                st.metric(ore, f"{qty:.0f} MT", f"{pct:.1f}%")

        st.divider()
        chem_df = pd.DataFrame({
            "Component": ["Fe%", "SiO2%", "Al2O3%", "CaO%", "MgO%",
                          "TiO2%", "P%", "MnO%", "Slag%"],
            "Value": [
                f"{result.fe_pct:.3f}%", f"{result.sio2_pct:.3f}%",
                f"{result.al2o3_pct:.3f}%", f"{result.cao_pct:.3f}%",
                f"{result.mgo_pct:.3f}%", f"{result.tio2_pct:.3f}%",
                f"{result.p_pct:.4f}%", f"{result.mno_pct:.3f}%",
                f"{result.slag_pct:.3f}%",
            ],
        })
        st.dataframe(chem_df, hide_index=True, width='stretch')


# ── Three single-goal cards in a row ─────────────────────────────────────────

def render_three_optimal_cards(anchors: dict):
    """
    Show Best Cost / Best Fe / Best Slag side by side as three cards.
    anchors: {goal_str: BlendResult}
    """
    goals = ["Minimize Cost", "Maximize Fe%", "Minimize Slag%"]
    labels = ["💰 BEST COST", "⬆️ BEST Fe%", "⬇️ BEST SLAG"]
    colors = ["#4FC3F7", "#81C784", "#CE93D8"]

    cols = st.columns(3)
    for col, goal, label, color in zip(cols, goals, labels, colors):
        result = anchors.get(goal)
        if result is None:
            col.error(f"No result for {goal}")
            continue
        with col:
            st.markdown(f"""
            <div style='background:#161B22; border:1px solid {color};
                        border-radius:10px; padding:1rem; margin-bottom:0.5rem;'>
                <span style='color:{color}; font-family:monospace;
                             font-size:0.78rem; letter-spacing:1.5px;'>
                    {label}
                </span>
            </div>
            """, unsafe_allow_html=True)
            st.metric("Fe%",      f"{result.fe_pct:.2f}%")
            st.metric("Slag%",    f"{result.slag_pct:.2f}%")
            st.metric("Cost/MT",  f"₹{result.cost_per_mt:,.0f}")
            st.metric("Slag MT",  f"{result.slag_mt:.1f}")
            with st.expander("Quantities"):
                for ore, qty in result.quantities.items():
                    pct = qty / result.total_qty * 100
                    st.write(f"**{ore}**: {qty:.0f} MT ({pct:.1f}%)")


# ── Balanced results display ──────────────────────────────────────────────────

def render_balanced_results(balanced_df: pd.DataFrame,
                             anchors: dict,
                             selected_ores: list):
    """
    Display balanced optimization results:
      1. Three anchor cards (Best Cost / Fe / Slag)
      2. Explanation of the scoring method
      3. Top balanced blends table
      4. Detailed card for the #1 balanced blend
    """

    # ── How balanced scoring works ────────────────────────────────────────────
    st.markdown("""
    <div style='background:#161B22; border-left:4px solid #E8A020;
                border-radius:6px; padding:1rem 1.2rem; margin-bottom:1.2rem;'>
        <span style='color:#E8A020; font-family:monospace; font-size:0.8rem;
                     letter-spacing:1px;'>⚖️ HOW BALANCED SCORE IS CALCULATED</span><br>
        <span style='color:#8B949E; font-size:0.85rem;'>
        Each blend is scored across all three objectives simultaneously.
        Each metric is normalised 0–1 across all candidates, then averaged equally:
        <br><br>
        <code style='color:#C9D1D9;'>Balance Score = ( cost_norm + (1 − fe_norm) + slag_norm ) / 3</code>
        <br><br>
        Lower score = better balanced blend. Rank 1 is the blend that most evenly 
        excels across cost, iron grade, and slag reduction.
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Three anchor blends ───────────────────────────────────────────────────
    st.markdown("#### Reference Anchors — Individual Optima")
    st.caption("These are the best possible results for each individual goal. Balanced blends lie between them.")
    render_three_optimal_cards(anchors)

    st.divider()

    # ── Top balanced blends table ─────────────────────────────────────────────
    if balanced_df.empty:
        st.warning(
            "No common blends found across all three optimization runs. "
            "Try a smaller step size to generate more candidate blends."
        )
        return

    st.markdown("#### ⚖️ Top Balanced Blends")
    st.caption(
        f"{len(balanced_df)} blends scored and ranked by combined cost + Fe + slag performance. "
        "Rank 1 is the best balanced blend."
    )

    display_cols = [
        "Balance Score", "Fe%", "Slag%", "Slag (MT)", "Cost/MT (₹)", "Total Cost (₹)"
    ]
    display_cols = [c for c in display_cols if c in balanced_df.columns]
    show_df = balanced_df[display_cols].head(20).copy()

    # Format
    for col in show_df.columns:
        if col == "Balance Score":
            show_df[col] = show_df[col].apply(lambda x: f"{x:.4f}")
        elif "₹" in col or "Cost" in col:
            show_df[col] = show_df[col].apply(lambda x: f"₹{x:,.0f}")
        elif "%" in col:
            show_df[col] = show_df[col].apply(lambda x: f"{x:.3f}%")
        elif "MT" in col:
            show_df[col] = show_df[col].apply(lambda x: f"{x:.1f}")

    st.dataframe(show_df, width='stretch')

    st.divider()

    # ── Best balanced blend detailed card ─────────────────────────────────────
    st.markdown("#### ★ Recommended Balanced Blend — Rank 1")
    st.caption("This blend best balances cost efficiency, iron recovery, and slag reduction.")

    top = balanced_df.iloc[0]

    kpi_cols = st.columns(5)
    kpis = [
        ("Fe%",       f"{top['Fe%']:.2f}%"),
        ("Slag%",     f"{top['Slag%']:.2f}%"),
        ("Slag MT",   f"{top['Slag (MT)']:.1f}"),
        ("Cost/MT",   f"₹{top['Cost/MT (₹)']:,.0f}"),
        ("Balance",   f"{top['Balance Score']:.4f}"),
    ]
    for col, (label, val) in zip(kpi_cols, kpis):
        col.metric(label, val)

    st.markdown("**Blend Composition**")
    ore_cols = [c for c in balanced_df.columns if c.startswith("qty_")]
    qty_display = st.columns(len(ore_cols))
    total_qty = sum(top[c] for c in ore_cols if c in top)
    for i, col_name in enumerate(ore_cols):
        ore = col_name.replace("qty_", "")
        qty = top[col_name]
        pct = qty / total_qty * 100 if total_qty > 0 else 0
        with qty_display[i]:
            st.metric(ore, f"{qty:.0f} MT", f"{pct:.1f}%")

    # Score breakdown vs anchors
    st.divider()
    st.markdown("**How this blend compares to the individual optima**")

    comparison_rows = []
    for goal, result in anchors.items():
        if result is None:
            continue
        comparison_rows.append({
            "Objective":    goal,
            "Best Possible": f"Fe:{result.fe_pct:.2f}%  Slag:{result.slag_pct:.2f}%  ₹{result.cost_per_mt:,.0f}/MT",
            "Balanced Blend":f"Fe:{top['Fe%']:.2f}%  Slag:{top['Slag%']:.2f}%  ₹{top['Cost/MT (₹)']:,.0f}/MT",
        })

    if comparison_rows:
        st.dataframe(
            pd.DataFrame(comparison_rows),
            hide_index=True,
            width='stretch',
        )


# ── Single-goal top blends table ─────────────────────────────────────────────

def render_top_blends_table(grid_df: pd.DataFrame, goal: str):
    """Render the top blends comparison table for single-goal modes."""
    if grid_df.empty:
        st.info("No comparison blends generated. Try reducing step size or expanding availability.")
        return

    st.markdown(f"#### Top Blends — Sorted by: **{goal}**")
    st.caption(f"{len(grid_df)} valid blends found via grid search")

    display_cols = [
        "Fe%", "SiO2%", "Al2O3%", "CaO%", "MgO%", "TiO2%",
        "Slag%", "Slag (MT)", "Cost/MT (₹)", "Total Cost (₹)", "Total Qty (MT)"
    ]
    display_cols = [c for c in display_cols if c in grid_df.columns]
    show_df = grid_df[display_cols].head(20).copy()

    for col in show_df.columns:
        if "₹" in col or "Cost" in col:
            show_df[col] = show_df[col].apply(lambda x: f"₹{x:,.0f}")
        elif "%" in col:
            show_df[col] = show_df[col].apply(lambda x: f"{x:.3f}%")
        elif "MT" in col:
            show_df[col] = show_df[col].apply(lambda x: f"{x:.1f}")

    st.dataframe(show_df, width='stretch')