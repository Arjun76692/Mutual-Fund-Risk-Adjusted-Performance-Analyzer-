import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="MF Risk Analyser", layout="wide", page_icon="📊")

# ─── Load Data ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("Mutual_Funds_MAster_2025.xlsx")
    # Clean up
    df['scheme_code'] = df['scheme_code'].astype(str)
    df['drawdown_abs'] = df['drawdown'].abs()  # work with positive for display
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Upload `Mutual_Funds_MAster_2025.xlsx` to the same folder as this script.")
    st.stop()

# ─── Live NAV via mftool (called on demand in Tab 3) ─────────────────────────

# ─── Sidebar: Risk Filters ────────────────────────────────────────────────────
st.sidebar.title("⚙️ Risk Filters")
st.sidebar.markdown("Set your downside protection thresholds")

use_defaults = st.sidebar.toggle("Use PRD default filters", value=True)

if use_defaults:
    min_sharpe   = 0.5
    max_vol      = 16.0
    max_drawdown = 20.0   # abs %
    min_dmc      = 1.0
else:
    min_sharpe   = st.sidebar.slider("Min Sharpe Ratio", -2.0, 1.5, 0.5, 0.05)
    max_vol      = st.sidebar.slider("Max Volatility (%)", 8.0, 35.0, 16.0, 0.5)
    max_drawdown = st.sidebar.slider("Max Drawdown (abs %)", 5.0, 50.0, 20.0, 0.5)
    min_dmc      = st.sidebar.slider("Min Downmarket Capture", 0.0, 12.0, 1.0, 0.1)

st.sidebar.markdown("---")
st.sidebar.markdown("**Other Filters**")

categories = ["All"] + sorted(df['scheme_category'].dropna().unique().tolist())
sel_category = st.sidebar.selectbox("Category", categories)

plan_type = st.sidebar.radio("Plan", ["Both", "Direct", "Regular"])

show_cols = st.sidebar.multiselect(
    "Visible Metrics",
    ["sharpe_ratio", "volatility", "drawdown_abs", "cagr_3yrs", "cagr_5yrs", "downmarket_capture", "upmarket_capture"],
    default=["sharpe_ratio", "volatility", "drawdown_abs", "cagr_3yrs"]
)

# ─── Filter Logic ────────────────────────────────────────────────────────────
def apply_filters(data):
    f = data.copy()
    if sel_category != "All":
        f = f[f['scheme_category'] == sel_category]
    if plan_type != "Both":
        f = f[f['plan_type'] == plan_type]
    return f

def apply_risk_filters(data):
    f = data.copy()
    f = f[f['sharpe_ratio'] >= min_sharpe]
    f = f[f['volatility'] <= max_vol]
    f = f[f['drawdown_abs'] <= max_drawdown]
    f = f[f['downmarket_capture'] >= min_dmc]
    return f

base_df   = apply_filters(df)
risk_df   = apply_risk_filters(base_df)

# ─── Main Layout ─────────────────────────────────────────────────────────────
st.title("📊 Mutual Fund Risk Analyser")
st.caption("Based on 342 Large-Cap funds | PRD: Risk-Indicated Fund Discovery")

tab1, tab2, tab3 = st.tabs(["🆚 Side-by-Side Comparison", "📈 Scatter Explorer", "🔍 Fund Detail"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — SIDE BY SIDE
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    col_l, col_r = st.columns(2, gap="medium")

    # ── Left: Unfiltered (raw pick) ────────────────────────────────────
    with col_l:
        st.markdown("### 🗂️ All Funds — No Risk Filter")
        st.caption(f"{len(base_df)} funds | picking without downside protection")

        if not base_df.empty:
            display_cols = ['base_name', 'plan_type', 'fund_house'] + [c for c in show_cols if c in base_df.columns]
            rename_map = {
                'base_name': 'Fund', 'plan_type': 'Plan', 'fund_house': 'AMC',
                'sharpe_ratio': 'Sharpe', 'volatility': 'Vol %',
                'drawdown_abs': 'Max DD %', 'cagr_3yrs': '3Y CAGR %',
                'cagr_5yrs': '5Y CAGR %', 'downmarket_capture': 'DMC',
                'upmarket_capture': 'UMC'
            }
            st.dataframe(
                base_df[display_cols].rename(columns=rename_map).reset_index(drop=True),
                use_container_width=True, height=380
            )

            # Quick stats
            st.markdown("**Category stats (no filter)**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Avg Sharpe", f"{base_df['sharpe_ratio'].mean():.2f}")
            c2.metric("Avg Volatility", f"{base_df['volatility'].mean():.1f}%")
            c3.metric("Avg Max Drawdown", f"{base_df['drawdown_abs'].mean():.1f}%")

    # ── Right: Risk-filtered ────────────────────────────────────────────
    with col_r:
        st.markdown("### 🛡️ Risk-Filtered Funds")
        filter_summary = (
            f"Sharpe ≥ {min_sharpe} | Vol ≤ {max_vol}% | "
            f"Drawdown ≤ {max_drawdown}% | DMC ≥ {min_dmc}"
        )
        st.caption(f"{len(risk_df)} funds pass | {filter_summary}")

        if not risk_df.empty:
            display_cols = ['base_name', 'plan_type', 'fund_house'] + [c for c in show_cols if c in risk_df.columns]
            st.dataframe(
                risk_df[display_cols].rename(columns=rename_map).reset_index(drop=True),
                use_container_width=True, height=380
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Avg Sharpe", f"{risk_df['sharpe_ratio'].mean():.2f}",
                      delta=f"{risk_df['sharpe_ratio'].mean() - base_df['sharpe_ratio'].mean():.2f} vs unfiltered")
            c2.metric("Avg Volatility", f"{risk_df['volatility'].mean():.1f}%",
                      delta=f"{risk_df['volatility'].mean() - base_df['volatility'].mean():.1f}%", delta_color="inverse")
            c3.metric("Avg Max Drawdown", f"{risk_df['drawdown_abs'].mean():.1f}%",
                      delta=f"{risk_df['drawdown_abs'].mean() - base_df['drawdown_abs'].mean():.1f}%", delta_color="inverse")
        else:
            st.warning("No funds pass current filters. Try relaxing them in the sidebar.")

    st.markdown("---")

    # ── Return vs Risk Bar Chart ─────────────────────────────────────────
    st.markdown("#### Return vs Risk: Filtered vs Unfiltered")

    compare_data = []
    for label, data in [("All Funds", base_df), ("Risk-Filtered", risk_df)]:
        compare_data.append({
            "Group": label,
            "3Y CAGR %": data['cagr_3yrs'].mean(),
            "Volatility %": data['volatility'].mean(),
            "Max Drawdown %": data['drawdown_abs'].mean(),
            "Sharpe Ratio": data['sharpe_ratio'].mean(),
        })
    cdf = pd.DataFrame(compare_data)

    metrics_to_plot = ["3Y CAGR %", "Volatility %", "Max Drawdown %", "Sharpe Ratio"]
    fig_bar = go.Figure()
    colors = {"All Funds": "#636EFA", "Risk-Filtered": "#00CC96"}

    for _, row in cdf.iterrows():
        fig_bar.add_trace(go.Bar(
            name=row['Group'],
            x=metrics_to_plot,
            y=[row[m] for m in metrics_to_plot],
            marker_color=colors[row['Group']],
            text=[f"{row[m]:.2f}" for m in metrics_to_plot],
            textposition='auto'
        ))

    fig_bar.update_layout(
        barmode='group', height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Nifty 50 Benchmark band ──────────────────────────────────────────
    st.markdown("#### 📌 Nifty 50 Benchmark Context")
    nifty_3y_cagr = 12.5  # approximate 3Y CAGR from dataset's index funds
    nifty_vol     = 14.2
    nifty_sharpe  = 0.62

    nifty_funds = df[df['base_name'].str.contains('Nifty 50', na=False) & (df['scheme_category'].str.contains('Index', na=False))]
    if not nifty_funds.empty:
        nifty_3y_cagr = nifty_funds['cagr_3yrs'].mean()
        nifty_vol     = nifty_funds['volatility'].mean()
        nifty_sharpe  = nifty_funds['sharpe_ratio'].mean()

    nc1, nc2, nc3, nc4 = st.columns(4)
    nc1.metric("Nifty 50 3Y CAGR", f"{nifty_3y_cagr:.1f}%")
    nc2.metric("Nifty 50 Volatility", f"{nifty_vol:.1f}%")
    nc3.metric("Nifty 50 Sharpe", f"{nifty_sharpe:.2f}")
    nc4.metric("Risk-Filtered beats Nifty CAGR?",
               "✅ Yes" if (not risk_df.empty and risk_df['cagr_3yrs'].mean() > nifty_3y_cagr) else "❌ No")




# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — SCATTER EXPLORER
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 📈 Volatility vs CAGR Scatter (Category View)")
    st.caption("Bubble size = Sharpe Ratio | Color = passes risk filter")

    plot_df = base_df.copy().dropna(subset=['volatility', 'cagr_3yrs', 'sharpe_ratio'])
    plot_df['passes_filter'] = plot_df['scheme_code'].isin(risk_df['scheme_code'])
    plot_df['passes_filter_label'] = plot_df['passes_filter'].map({True: "✅ Passes Filter", False: "❌ Filtered Out"})
    plot_df['bubble_size'] = (plot_df['sharpe_ratio'].clip(lower=0) * 15 + 5)

    fig_scatter = px.scatter(
        plot_df,
        x='volatility', y='cagr_3yrs',
        color='passes_filter_label',
        size='bubble_size',
        hover_name='base_name',
        hover_data={'volatility': ':.1f', 'cagr_3yrs': ':.2f',
                    'sharpe_ratio': ':.2f', 'drawdown_abs': ':.1f',
                    'bubble_size': False, 'passes_filter_label': False},
        color_discrete_map={"✅ Passes Filter": "#00CC96", "❌ Filtered Out": "#EF553B"},
        labels={'volatility': 'Annualised Volatility (%)', 'cagr_3yrs': '3Y CAGR (%)'},
        height=500
    )

    # Add Nifty benchmark lines
    if not nifty_funds.empty:
        fig_scatter.add_vline(x=nifty_vol, line_dash="dash", line_color="gray",
                              annotation_text=f"Nifty Vol ({nifty_vol:.1f}%)")
        fig_scatter.add_hline(y=nifty_3y_cagr, line_dash="dash", line_color="gray",
                              annotation_text=f"Nifty CAGR ({nifty_3y_cagr:.1f}%)")

    fig_scatter.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Downside capture vs upside capture
    st.markdown("### ⬆️⬇️ Upmarket vs Downmarket Capture")
    st.caption("Top-right = high upside, low downside capture = ideal")

    cap_df = base_df.dropna(subset=['upmarket_capture', 'downmarket_capture', 'cagr_3yrs'])
    cap_df = cap_df[cap_df['downmarket_capture'] > 0]  # remove bad data
    cap_df['passes_filter'] = cap_df['scheme_code'].isin(risk_df['scheme_code'])
    cap_df['label'] = cap_df['passes_filter'].map({True: "✅ Passes Filter", False: "❌ Filtered Out"})

    fig_cap = px.scatter(
        cap_df,
        x='downmarket_capture', y='upmarket_capture',
        color='label',
        hover_name='base_name',
        hover_data={'cagr_3yrs': ':.2f', 'sharpe_ratio': ':.2f'},
        color_discrete_map={"✅ Passes Filter": "#00CC96", "❌ Filtered Out": "#EF553B"},
        labels={'downmarket_capture': 'Downmarket Capture', 'upmarket_capture': 'Upmarket Capture'},
        height=420
    )
    st.plotly_chart(fig_cap, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — FUND DETAIL + RISK CARD
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🔍 Fund Risk Card")
    st.caption("Search any fund and see a PRD-style Risk Score Card")

    # Selector
    all_fund_names = base_df['base_name'].dropna().unique().tolist()
    selected_fund = st.selectbox("Select a Fund", sorted(all_fund_names))

    fund_row = base_df[base_df['base_name'] == selected_fund].iloc[0]

    passes = (
        fund_row['sharpe_ratio'] >= min_sharpe and
        fund_row['volatility'] <= max_vol and
        fund_row['drawdown_abs'] <= max_drawdown and
        fund_row['downmarket_capture'] >= min_dmc
    )

    badge = "🟢 Passes Your Risk Filter" if passes else "🔴 Fails Your Risk Filter"
    st.markdown(f"## {selected_fund}")
    st.markdown(f"**{badge}**  |  {fund_row['fund_house']}  |  {fund_row['plan_type']}  |  {fund_row['scheme_category']}")

    # Risk Score Card
    st.markdown("---")
    st.markdown("#### Risk Score Card")
    r1, r2, r3, r4 = st.columns(4)

    def metric_color(val, threshold, higher_is_better=True):
        if higher_is_better:
            return "normal" if val >= threshold else "inverse"
        else:
            return "normal" if val <= threshold else "inverse"

    r1.metric(
        "Sharpe Ratio",
        f"{fund_row['sharpe_ratio']:.2f}",
        delta=f"threshold: {min_sharpe}",
        delta_color=metric_color(fund_row['sharpe_ratio'], min_sharpe, True)
    )
    r2.metric(
        "Volatility",
        f"{fund_row['volatility']:.1f}%",
        delta=f"threshold: {max_vol}%",
        delta_color=metric_color(fund_row['volatility'], max_vol, False)
    )
    r3.metric(
        "Max Drawdown",
        f"{fund_row['drawdown_abs']:.1f}%",
        delta=f"threshold: {max_drawdown}%",
        delta_color=metric_color(fund_row['drawdown_abs'], max_drawdown, False)
    )
    r4.metric(
        "Downmarket Capture",
        f"{fund_row['downmarket_capture']:.2f}",
        delta=f"threshold: {min_dmc}",
        delta_color=metric_color(fund_row['downmarket_capture'], min_dmc, True)
    )

    # Return metrics
    st.markdown("#### Return Metrics")
    ret1, ret2, ret3, ret4 = st.columns(4)
    ret1.metric("3Y CAGR", f"{fund_row['cagr_3yrs']:.2f}%" if pd.notna(fund_row['cagr_3yrs']) else "N/A")
    ret2.metric("5Y CAGR", f"{fund_row['cagr_5yrs']:.2f}%" if pd.notna(fund_row['cagr_5yrs']) else "N/A")
    ret3.metric("Current NAV", f"₹{fund_row['current_nav']:.2f}" if pd.notna(fund_row['current_nav']) else "N/A")
    ret4.metric("Fund Age", f"{fund_row['fund_age_years']} yrs")

    # Plain language tooltips (PRD requirement)
    st.markdown("---")
    with st.expander("📖 What do these metrics mean? (Plain language)"):
        st.markdown("""
**Sharpe Ratio** — How much return you get *per unit of risk*. Higher = better. 
A Sharpe of 1.0 means the fund earns 1% extra return for every 1% of risk it takes.  
*Rule of thumb: > 0.5 is decent, > 1.0 is good.*

**Volatility** — How much the fund's NAV swings up and down in a year, as a %.  
A 16% volatility means the fund could swing ±16% from its average in a normal year.  
*Lower = more stable.*

**Max Drawdown** — The worst peak-to-trough drop the fund has experienced (shown as %).  
If your fund had a max drawdown of 25%, it once fell from ₹100 to ₹75 before recovering.  
*Lower = better downside protection.*

**Downmarket Capture** — When the market falls, how much of that fall does this fund absorb?  
A DMC of 0.8 means the fund drops only 80% as much as the benchmark when markets go down.  
*Higher number in our dataset = better (fund holds up more during market drops).*
        """)

    # Compare to category peers
    st.markdown("#### vs Category Peers")
    cat_peers = base_df[base_df['scheme_category'] == fund_row['scheme_category']].dropna(subset=['sharpe_ratio', 'volatility'])

    if len(cat_peers) > 1:
        fig_radar = go.Figure()

        metrics = ['sharpe_ratio', 'volatility', 'drawdown_abs', 'cagr_3yrs']
        metric_labels = ['Sharpe', 'Volatility', 'Max DD', '3Y CAGR']

        # Percentile rank within category
        percentiles_fund = []
        percentiles_median = []
        for m in metrics:
            vals = cat_peers[m].dropna()
            pct = (vals < fund_row[m]).sum() / len(vals) * 100
            percentiles_fund.append(round(pct, 1))
            percentiles_median.append(50.0)

        fig_radar.add_trace(go.Scatterpolar(
            r=percentiles_fund, theta=metric_labels + [metric_labels[0]],
            fill='toself', name=selected_fund[:30],
            line_color='#00CC96'
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=percentiles_median + [percentiles_median[0]], theta=metric_labels + [metric_labels[0]],
            fill='toself', name='Median Peer',
            line_color='#636EFA', opacity=0.4
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(range=[0, 100], ticksuffix="th pct")),
            height=380, showlegend=True,
            title="Percentile Rank within Category (higher = better ranked)"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # Live NAV section
    st.markdown("---")
    st.markdown("#### 📡 Live NAV & Historical Performance")
    code = str(fund_row['scheme_code'])

    if st.button(f"Fetch Live NAV + 1Y History for {code}"):
        with st.spinner("Fetching from AMFI via mftool..."):
            try:
                from mftool import Mftool
                mf = Mftool()

                # Current NAV
                quote = mf.get_scheme_quote(code)
                if quote and 'nav' in quote:
                    st.success(f"✅ Live NAV: ₹{float(quote['nav']):.4f}  |  Last updated: {quote.get('last_updated', 'N/A')}")
                else:
                    st.info(f"Stored NAV: ₹{fund_row['current_nav']:.2f}")

                # Historical NAV chart
                hist_df = mf.get_scheme_historical_nav(code, as_Dataframe=True)
                if hist_df is not None and not hist_df.empty:
                    hist_df.index = pd.to_datetime(hist_df.index, dayfirst=True, errors='coerce')
                    hist_df = hist_df.sort_index().dropna()
                    hist_df['nav'] = pd.to_numeric(hist_df['nav'], errors='coerce')
                    hist_1y = hist_df[hist_df.index >= (hist_df.index.max() - pd.DateOffset(years=1))]

                    fig_nav = go.Figure()
                    fig_nav.add_trace(go.Scatter(
                        x=hist_1y.index, y=hist_1y['nav'],
                        mode='lines', name='NAV',
                        line=dict(color='#00CC96', width=2),
                        fill='tozeroy', fillcolor='rgba(0,204,150,0.1)'
                    ))
                    fig_nav.update_layout(
                        title="1-Year NAV History",
                        xaxis_title="Date", yaxis_title="NAV (₹)",
                        height=320, margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig_nav, use_container_width=True)

                    # vs Nifty 50 index fund (first one we find)
                    nifty_ref = df[
                        df['base_name'].str.contains('Nifty 50', na=False) &
                        df['scheme_category'].str.contains('Index', na=False) &
                        (df['plan_type'] == fund_row['plan_type'])
                    ]
                    if not nifty_ref.empty:
                        nifty_code = str(nifty_ref.iloc[0]['scheme_code'])
                        nifty_hist = mf.get_scheme_historical_nav(nifty_code, as_Dataframe=True)
                        if nifty_hist is not None and not nifty_hist.empty:
                            nifty_hist.index = pd.to_datetime(nifty_hist.index, dayfirst=True, errors='coerce')
                            nifty_hist = nifty_hist.sort_index().dropna()
                            nifty_hist['nav'] = pd.to_numeric(nifty_hist['nav'], errors='coerce')

                            # Normalize both to 100 at start
                            common_start = max(hist_1y.index.min(), nifty_hist.index.min())
                            f_norm = hist_1y[hist_1y.index >= common_start]['nav']
                            n_norm = nifty_hist[nifty_hist.index >= common_start]['nav']

                            if not f_norm.empty and not n_norm.empty:
                                f_norm = f_norm / f_norm.iloc[0] * 100
                                n_norm = n_norm / n_norm.iloc[0] * 100

                                fig_cmp = go.Figure()
                                fig_cmp.add_trace(go.Scatter(
                                    x=f_norm.index, y=f_norm.values,
                                    name=selected_fund[:40], line=dict(color='#00CC96', width=2)
                                ))
                                fig_cmp.add_trace(go.Scatter(
                                    x=n_norm.index, y=n_norm.values,
                                    name='Nifty 50 Index (benchmark)',
                                    line=dict(color='#636EFA', width=2, dash='dash')
                                ))
                                fig_cmp.update_layout(
                                    title="1-Year Return vs Nifty 50 Benchmark (Indexed to 100)",
                                    xaxis_title="Date", yaxis_title="Indexed Return",
                                    height=340, margin=dict(l=20, r=20, t=40, b=20),
                                    legend=dict(orientation="h", y=1.1)
                                )
                                st.plotly_chart(fig_cmp, use_container_width=True)

            except Exception as e:
                st.error(f"mftool error: {e}")
                st.info(f"Stored NAV from dataset: ₹{fund_row['current_nav']:.2f}")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Data: Mutual_Funds_MAster_2025.xlsx (342 Large-Cap funds) | "
    "PRD: Risk-Indicated Fund Discovery | Live NAV via mftool + AMFI"
)