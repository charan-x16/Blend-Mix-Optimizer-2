"""
Ore Blend Mix Optimization System
BF-02 Blast Furnace — Bunker Ore Blend Optimizer
"""

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Ore Blend Optimizer — BF-02",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
    .main { background-color: #0D1117; color: #C9D1D9; }
    .stApp { background-color: #0D1117; }
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #21262D;
    }
    [data-testid="stSidebar"] * { color: #C9D1D9 !important; }
    .stMetric {
        background: #161B22;
        border: 1px solid #21262D;
        border-radius: 8px;
        padding: 1rem;
    }
    .stMetric label {
        color: #8B949E !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 0.75rem !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #E8A020 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 1.4rem !important;
    }
    .stMetric [data-testid="stMetricDelta"] { color: #8B949E !important; font-size: 0.75rem !important; }
    .stButton > button {
        background: linear-gradient(135deg, #E8A020, #c17d10) !important;
        color: #0D1117 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 6px !important;
        letter-spacing: 1px;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #f5b53a, #E8A020) !important;
        transform: translateY(-1px);
    }
    .stDataFrame { border: 1px solid #21262D; border-radius: 8px; }
    h1, h2, h3, h4 { font-family: 'Share Tech Mono', monospace !important; color: #C9D1D9 !important; }
    h1 { color: #E8A020 !important; letter-spacing: 2px; }
    .stTabs [data-baseweb="tab"] { font-family: 'Share Tech Mono', monospace; color: #8B949E; }
    .stTabs [aria-selected="true"] { color: #E8A020 !important; border-bottom: 2px solid #E8A020 !important; }
    .stAlert { border-radius: 8px; }
    div[data-testid="stExpander"] { background: #161B22; border: 1px solid #21262D; border-radius: 8px; }
    hr { border-color: #21262D !important; }
</style>
""", unsafe_allow_html=True)

from data.ore_chemistry import load_ore_chemistry
from engine.optimizer import run_optimizer
from engine.grid_search import run_grid_search, estimate_combination_count
from engine.balanced_optimizer import run_balanced_optimization
from ui.sidebar import render_sidebar
from ui.results import (
    render_best_blend_card,
    render_top_blends_table,
    render_balanced_results,
)
from ui.charts import (
    render_pareto_scatter,
    render_composition_bar,
    render_radar_chart,
    render_fe_contribution_waterfall,
)


@st.cache_data
def load_data():
    return load_ore_chemistry()


def render_header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        <h1 style='margin-bottom:0;'>⚙ ORE BLEND OPTIMIZER</h1>
        <p style='color:#8B949E; font-family:monospace; margin-top:0.2rem; font-size:0.85rem;'>
            BF-02 BUNKER — BLAST FURNACE BLEND OPTIMIZATION SYSTEM
        </p>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style='text-align:right; padding-top:0.5rem;'>
            <span style='font-family:monospace; font-size:0.75rem; color:#8B949E;'>
                FY 2025–26 | AVERAGE CHEMISTRY
            </span>
        </div>
        """, unsafe_allow_html=True)
    st.divider()


def render_catalogue_tab(chemistry_df: pd.DataFrame):
    st.markdown("#### 📋 Ore Chemistry Reference — BF-02 Bunker (2025-26 Averages)")
    display_cols = ["%Fe(T)", "%SiO2", "%Al2O3", "%CaO", "%MgO", "%TiO2", "%P", "%MnO", "%LOI", "Slag%"]
    display_cols = [c for c in display_cols if c in chemistry_df.columns]
    st.dataframe(
        chemistry_df[display_cols].style.format("{:.3f}"),
        width='stretch',
        height=480,
    )
    st.caption("Slag% = SiO2% + Al2O3% + CaO% + MgO%")
    with st.expander("ℹ️ Special Ore Notes"):
        st.markdown("""
        - **Acore Industries** — Mn ore (MnO ~22%). Very low Fe (~27%). Use only if Mn addition is intentional.
        - **Titani Ferrous CLO** — TiO2 ~12.2%. High titanium loads slag and can damage furnace lining.
        - **NMDC Donimalai** — SiO2 ~14.4%. Heavy slag burden if used in large quantities.
        - **Sinter (SP-02)** — Self-fluxing. High CaO (~10.6%) reduces external limestone need.
        """)


def main():
    chemistry_df = load_data()
    render_header()

    operator_inputs = render_sidebar(chemistry_df)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Ore Catalogue",
        "★ Optimal Blend",
        "📊 Comparison Charts",
        "🎯 Blend Comparison",
    ])

    with tab1:
        render_catalogue_tab(chemistry_df)

    if operator_inputs is None:
        with tab2:
            st.markdown("""
            <div style='text-align:center; padding:4rem 2rem; color:#8B949E;'>
                <h2 style='color:#8B949E; font-family:monospace;'>← Configure blend in sidebar</h2>
                <p>Select ores · Enter quantities & prices · Pick goal · Click RUN OPTIMIZER</p>
            </div>
            """, unsafe_allow_html=True)
        with tab3:
            st.info("Run the optimizer first to see charts.")
        with tab4:
            st.info("Run the optimizer first to compare blends.")
        return

    selected_ores  = operator_inputs["selected_ores"]
    max_quantities = operator_inputs["max_quantities"]
    prices         = operator_inputs["prices"]
    target_qty     = operator_inputs["target_qty"]
    goal           = operator_inputs["goal"]
    step_size      = operator_inputs["step_size"]

    # ═══════════════════════════════════════════════════════════════════════
    # BALANCED OPTIMIZATION PATH
    # ═══════════════════════════════════════════════════════════════════════
    if goal == "Balanced Optimization":
        with st.spinner("Running balanced optimization (3 LP objectives + grid search)..."):
            balanced_df, anchors = run_balanced_optimization(
                selected_ores=selected_ores,
                max_quantities=max_quantities,
                prices=prices,
                target_qty=target_qty,
                step_size=step_size,
                chemistry_df=chemistry_df,
            )

        with tab2:
            render_balanced_results(balanced_df, anchors, selected_ores)

        with tab3:
            if not balanced_df.empty:
                st.markdown("#### Pareto Front — All Balanced Candidate Blends")
                # Use best Fe anchor for waterfall
                best_fe = anchors.get("Maximize Fe%")
                if best_fe:
                    render_pareto_scatter(balanced_df, best_fe)
                    st.divider()
                    st.markdown("#### Fe% Contribution per Ore — Best Fe Blend")
                    render_fe_contribution_waterfall(best_fe, chemistry_df)
                st.divider()
                st.markdown("#### Blend Composition — Top 10 Balanced Blends")
                render_composition_bar(balanced_df, selected_ores, top_n=10)
            else:
                st.info("No balanced blend candidates. Try a smaller step size.")

        with tab4:
            if not balanced_df.empty:
                st.markdown("#### Compare Balanced Blends")
                max_rank = min(20, len(balanced_df))
                selected_ranks = st.multiselect(
                    "Select ranks to compare (2–5 blends)",
                    options=list(range(1, max_rank + 1)),
                    default=[1, 2, 3] if max_rank >= 3 else list(range(1, max_rank + 1)),
                    max_selections=5,
                )
                if selected_ranks:
                    best_fe = anchors.get("Maximize Fe%")
                    if best_fe:
                        render_radar_chart(balanced_df, selected_ranks, best_fe)
                    st.divider()
                    _render_comparison_table(balanced_df, selected_ranks)
            else:
                st.info("No balanced blend results to compare.")
        return

    # ═══════════════════════════════════════════════════════════════════════
    # SINGLE-GOAL OPTIMIZATION PATH
    # ═══════════════════════════════════════════════════════════════════════
    with st.spinner(f"Running optimizer: {goal}..."):
        optimal_result = run_optimizer(
            selected_ores=selected_ores,
            max_quantities=max_quantities,
            prices=prices,
            target_qty=target_qty,
            goal=goal,
            chemistry_df=chemistry_df,
        )

    if optimal_result is None:
        st.error("❌ Optimizer could not find a feasible solution. Check total available ≥ target.")
        return

    est_count = estimate_combination_count(
        selected_ores, optimal_result.quantities, max_quantities, target_qty, step_size
    )

    with st.spinner(f"Running grid search (~{est_count} combinations)..."):
        grid_df = run_grid_search(
            selected_ores=selected_ores,
            optimal_quantities=optimal_result.quantities,
            max_quantities=max_quantities,
            prices=prices,
            target_qty=target_qty,
            step_size=step_size,
            goal=goal,
            chemistry_df=chemistry_df,
        )

    with tab2:
        render_best_blend_card(optimal_result, goal)
        st.divider()
        render_top_blends_table(grid_df, goal)

    with tab3:
        if not grid_df.empty:
            st.markdown("#### Pareto Front — All Valid Blends")
            render_pareto_scatter(grid_df, optimal_result)
            st.divider()
            st.markdown("#### Fe% Contribution per Ore")
            render_fe_contribution_waterfall(optimal_result, chemistry_df)
            st.divider()
            st.markdown("#### Blend Composition — Top 10 Blends")
            render_composition_bar(grid_df, selected_ores, top_n=10)
        else:
            st.info("No grid search results. Try a smaller step size.")

    with tab4:
        if not grid_df.empty:
            max_rank = min(20, len(grid_df))
            selected_ranks = st.multiselect(
                "Select ranks to compare (2–5 blends)",
                options=list(range(1, max_rank + 1)),
                default=[1, 2, 3] if max_rank >= 3 else list(range(1, max_rank + 1)),
                max_selections=5,
            )
            if selected_ranks:
                render_radar_chart(grid_df, selected_ranks, optimal_result)
                st.divider()
                _render_comparison_table(grid_df, selected_ranks, optimal_result)
        else:
            st.info("No results to compare.")


def _render_comparison_table(grid_df: pd.DataFrame, selected_ranks: list,
                              optimal_result=None):
    """Side-by-side chemistry comparison table."""
    st.markdown("#### Side-by-Side Chemistry Comparison")
    rows = []

    if optimal_result:
        rows.append({
            "Blend": "★ Optimal",
            "Fe%": optimal_result.fe_pct,
            "SiO2%": optimal_result.sio2_pct,
            "Al2O3%": optimal_result.al2o3_pct,
            "CaO%": optimal_result.cao_pct,
            "MgO%": optimal_result.mgo_pct,
            "TiO2%": optimal_result.tio2_pct,
            "Slag%": optimal_result.slag_pct,
            "Slag MT": optimal_result.slag_mt,
            "Cost/MT (₹)": optimal_result.cost_per_mt,
        })

    for rank in selected_ranks:
        if 1 <= rank <= len(grid_df):
            row = grid_df.iloc[rank - 1]
            rows.append({
                "Blend": f"Rank {rank}",
                "Fe%": row["Fe%"],
                "SiO2%": row["SiO2%"],
                "Al2O3%": row["Al2O3%"],
                "CaO%": row["CaO%"],
                "MgO%": row["MgO%"],
                "TiO2%": row["TiO2%"],
                "Slag%": row["Slag%"],
                "Slag MT": row["Slag (MT)"],
                "Cost/MT (₹)": row["Cost/MT (₹)"],
            })

    if rows:
        compare_df = pd.DataFrame(rows).set_index("Blend")
        st.dataframe(compare_df.style.format("{:.3f}"), width='stretch')


if __name__ == "__main__":
    main()