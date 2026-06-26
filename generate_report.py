"""
GTF Grounding Tracker — single-command report generator.
Run: python generate_report.py
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

 
# Paths
 
ROOT = Path(__file__).parent
DATA_FILE        = ROOT / "data" / "grounding_counts.csv"
COMMS_FILE       = ROOT / "data" / "wizz_air_comms.csv"
GROUND_DAY_FILE  = ROOT / "data" / "ground_day_comparison.csv"
VARIANT_FILE     = ROOT / "data" / "variant_split.csv"
REPORT_FILE = ROOT / "index.html"

 
# Colour palette
 
PALETTE = {
    "primary": "#1a6fb5",
    "accent":  "#e85d26",
    "mid":     "#2eaa6e",
    "muted":   "#8da9c4",
    "bg":      "#f7f9fc",
}

 
# Load data
 
print("Loading data …")
df = pd.read_csv(DATA_FILE, parse_dates=["date"])
df["airline"] = df["airline"].str.strip()
df_global   = df[df["airline"] == "Global"].sort_values("date").copy()
df_airlines = df[df["airline"] != "Global"].copy()

df_comms = pd.read_csv(COMMS_FILE, parse_dates=["date"])
df_comms = df_comms.sort_values("date").reset_index(drop=True)
df_wizz  = df_airlines[df_airlines["airline"] == "Wizz Air"].sort_values("date").copy()

df_ground_day = pd.read_csv(GROUND_DAY_FILE, parse_dates=["as_of_date"])
df_variant    = pd.read_csv(VARIANT_FILE, parse_dates=["as_of_date"])


 
# Shared layout defaults
 
BASE_LAYOUT = dict(
    paper_bgcolor=PALETTE["bg"],
    plot_bgcolor=PALETTE["bg"],
    font=dict(family="system-ui, -apple-system, sans-serif", color="#333"),
    margin=dict(l=60, r=40, t=60, b=60),
    hoverlabel=dict(bgcolor="white", font_size=13),
)


def fig_to_div(fig: go.Figure, first: bool = False) -> str:
    """Return an HTML <div> string for embedding. CDN now loads once from <head>, never per-chart."""
    return pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": True, "responsive": True},
    )


 
# Chart 1 — Global grounding trend over time
 
def chart1() -> str:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_global["date"],
        y=df_global["grounded_aircraft"],
        mode="lines+markers+text",
        name="Aircraft Grounded",
        line=dict(color=PALETTE["primary"], width=2.5),
        marker=dict(size=9, color=PALETTE["primary"]),
        fill="tozeroy",
        fillcolor="rgba(26,111,181,0.10)",
        text=df_global["grounded_aircraft"].astype(int).astype(str),
        textposition="top center",
        textfont=dict(color=PALETTE["primary"], size=11),
        hovertemplate="<b>%{x|%b %Y}</b><br>Grounded: %{y}<extra></extra>",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="GTF Aircraft Grounded Globally Over Time", font=dict(size=15, color="#222")),
        xaxis=dict(title="Date", tickformat="%b %Y", showgrid=True, gridcolor="#e0e0e0"),
        yaxis=dict(title="Aircraft Grounded", range=[600, 920], dtick=50,
                   showgrid=True, gridcolor="#e0e0e0"),
        showlegend=False,
    )

    print("  Built chart 1")
    return fig_to_div(fig, first=True)


 
# Chart 2 — Most affected airlines (latest snapshot per airline)
 
def chart2() -> str:
    latest = (
        df_airlines
        .sort_values("date")
        .groupby("airline", as_index=False)
        .last()
        .sort_values("pct_grounded", ascending=True)
    )

    bar_colors = [
        PALETTE["accent"] if p >= 40 else
        PALETTE["primary"] if p >= 20 else
        PALETTE["mid"]
        for p in latest["pct_grounded"]
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=latest["airline"],
        x=latest["pct_grounded"],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v:.1f}%" for v in latest["pct_grounded"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Grounded: %{x:.1f}%<extra></extra>",
        name="",
    ))

    # Global-avg reference line
    fig.add_vline(x=30, line_dash="dash", line_color=PALETTE["muted"],
                  line_width=1.5,
                  annotation_text="Global avg ~34%",
                  annotation_position="top right",
                  annotation_font=dict(size=11, color=PALETTE["muted"]))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="% of GTF Fleet Grounded by Airline (Latest Data)", font=dict(size=15, color="#222")),
        xaxis=dict(title="% of GTF Fleet Grounded", range=[0, 60],
                   showgrid=True, gridcolor="#e0e0e0"),
        yaxis=dict(title=""),
        showlegend=False,
    )

    print("  Built chart 2")
    return fig_to_div(fig)


 
# Chart 3 — Groundings vs MRO Recovery (single shared % axis — FIXED)
# Original used two independently-scaled y-axes, which made the lines visually
# converge in a way that could be misread as "the problem is resolving."
# Both series are now normalized to % change from their own baseline on one
# shared axis, so visual distance is actually meaningful.
 
def chart3() -> str:
    ground_base = df_global.sort_values("date").iloc[0]["grounded_aircraft"]
    ground_pct_change = [(v / ground_base - 1) * 100 for v in df_global.sort_values("date")["grounded_aircraft"]]

    mro_dates = pd.to_datetime(["2024-01-01", "2025-01-01", "2025-10-01"])
    mro_values = [100, 126, 139]
    mro_pct_change = [(v / 100 - 1) * 100 for v in mro_values]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_global.sort_values("date")["date"], y=ground_pct_change,
        mode="lines+markers+text", name="Aircraft Grounded (% change from Oct 2024)",
        line=dict(color=PALETTE["accent"], width=2.5),
        marker=dict(size=9, color=PALETTE["accent"]),
        text=[f"+{v:.0f}%" for v in ground_pct_change], textposition="top center",
        textfont=dict(color=PALETTE["accent"], size=11),
        hovertemplate="<b>%{x|%b %Y}</b><br>Groundings: %{y:+.0f}%<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=mro_dates, y=mro_pct_change,
        mode="lines+markers+text", name="MRO Output Index (% change from 2024 baseline)",
        line=dict(color=PALETTE["primary"], width=2.5, dash="dash"),
        marker=dict(size=9, color=PALETTE["primary"], symbol="square"),
        text=[f"+{v:.0f}%" for v in mro_pct_change], textposition="bottom center",
        textfont=dict(color=PALETTE["primary"], size=11),
        hovertemplate="<b>%{x|%b %Y}</b><br>MRO output: %{y:+.0f}%<extra></extra>",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Groundings vs MRO Recovery — Both on the Same % Scale", font=dict(size=15, color="#222")),
        xaxis=dict(title="Date", tickformat="%b %Y", showgrid=True, gridcolor="#e0e0e0"),
        yaxis=dict(title="% Change from Baseline", showgrid=True, gridcolor="#e0e0e0",
                   zeroline=True, zerolinecolor="#999"),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.85)", borderwidth=1),
        annotations=[dict(
            font=dict(color="#999", size=10), showarrow=False,
            text="Both series shown as % change from their own Oct 2024 / 2024 baseline on one shared axis. Groundings rising faster than MRO output recovers means the gap is still widening in absolute terms, not closing — the lines are not converging toward resolution.",
            x=0, xanchor="left", xref="paper", y=-0.22, yref="paper",
        )],
    )

    print("  Built chart 3 (fixed: single shared axis)")
    return fig_to_div(fig)


 
# Sentiment helpers
 
SENTIMENT_COLOR = {
    1: "#d62728",   # very pessimistic — red
    2: "#ff7f0e",   # pessimistic — orange
    3: "#bcbd22",   # neutral — gold
    4: "#2eaa6e",   # optimistic — green  (reuse PALETTE mid)
    5: "#17becf",   # very optimistic — teal
}
SENTIMENT_LABEL = {
    1: "Very Pessimistic",
    2: "Pessimistic",
    3: "Neutral",
    4: "Optimistic",
    5: "Very Optimistic",
}


 
# Chart 4 — Wizz Air grounding trajectory vs PR moments
 
def chart4() -> str:
    fig = go.Figure()

    # Grounding line
    fig.add_trace(go.Scatter(
        x=df_wizz["date"],
        y=df_wizz["grounded_aircraft"],
        mode="lines+markers",
        name="Aircraft Grounded (actual)",
        line=dict(color=PALETTE["primary"], width=2.5),
        marker=dict(size=9, color=PALETTE["primary"]),
        fill="tozeroy",
        fillcolor="rgba(26,111,181,0.08)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Grounded: %{y}<extra></extra>",
    ))

    # PR event markers, coloured by sentiment
    for _, row in df_comms.iterrows():
        score = int(row["sentiment_score"])
        color = SENTIMENT_COLOR.get(score, "#888")
        label = SENTIMENT_LABEL.get(score, "")
        short_headline = row["headline"][:55] + ("…" if len(row["headline"]) > 55 else "")
        fig.add_trace(go.Scatter(
            x=[row["date"]],
            y=[0],
            mode="markers",
            name=short_headline,
            marker=dict(size=14, color=color, symbol="star", line=dict(color="white", width=1)),
            hovertemplate=(
                f"<b>{row['date'].strftime('%b %Y')}</b><br>"
                f"<b>{row['source_type'].replace('_', ' ').title()}</b><br>"
                f"{row['headline']}<br>"
                f"Sentiment: {label}<br>"
                f"<i>{row['key_claim'][:120]}…</i><extra></extra>"
            ),
            showlegend=False,
        ))

    # Claimed resolution timeline annotations — use shape + annotation separately
    # (add_vline with string x values is unreliable in older Plotly builds)
    timeline_claims = [
        (pd.Timestamp("2026-01-01"), "Original target: end-2026", PALETTE["mid"]),
        (pd.Timestamp("2027-01-01"), "Revised target: end-2027", PALETTE["accent"]),
    ]
    for ts, label_text, color in timeline_claims:
        x_ms = ts.value // 10**6   # epoch milliseconds for Plotly shapes
        fig.add_shape(
            type="line",
            x0=x_ms, x1=x_ms, y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(dash="dot", color=color, width=1.5),
        )
        fig.add_annotation(
            x=x_ms, y=0.98, xref="x", yref="paper",
            text=label_text, showarrow=False,
            font=dict(size=10, color=color),
            xanchor="left", yanchor="top",
            bgcolor="rgba(255,255,255,0.7)",
        )

    # Sentiment legend as invisible dummy traces
    for score, label in SENTIMENT_LABEL.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=10, color=SENTIMENT_COLOR[score], symbol="star"),
            name=f"PR: {label}",
            showlegend=True,
        ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Wizz Air: Grounding Trajectory vs Public Narrative Moments", font=dict(size=15, color="#222")),
        xaxis=dict(title="Date", tickformat="%b %Y", showgrid=True, gridcolor="#e0e0e0"),
        yaxis=dict(title="Wizz Air Aircraft Grounded", range=[0, 65],
                   showgrid=True, gridcolor="#e0e0e0"),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.85)", borderwidth=1,
                    font=dict(size=10)),
    )

    print("  Built chart 4")
    return fig_to_div(fig)


 
# Chart 5 — Ground-day comparison: GTF vs Leap vs older engines
 
def chart5() -> str:
    df_gd = df_ground_day.copy()
    df_gd["mid"] = (df_gd["ground_day_pct_low"] + df_gd["ground_day_pct_high"]) / 2
    df_gd["range_label"] = df_gd.apply(
        lambda r: f"{r['ground_day_pct_low']:.0f}%" if r["ground_day_pct_low"] == r["ground_day_pct_high"]
        else f"{r['ground_day_pct_low']:.0f}–{r['ground_day_pct_high']:.0f}%",
        axis=1,
    )

    bar_colors = [PALETTE["accent"], PALETTE["mid"], PALETTE["muted"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_gd["engine_family"],
        x=df_gd["mid"],
        orientation="h",
        marker_color=bar_colors[: len(df_gd)],
        text=df_gd["range_label"],
        textposition="outside",
        error_x=dict(
            type="data",
            symmetric=False,
            array=df_gd["ground_day_pct_high"] - df_gd["mid"],
            arrayminus=df_gd["mid"] - df_gd["ground_day_pct_low"],
            color="#888",
            thickness=1.2,
        ),
        hovertemplate="<b>%{y}</b><br>Ground-day rate: %{text}<extra></extra>",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Ground-Day Rate: GTF vs Competing Engine Families", font=dict(size=15, color="#222")),
        xaxis=dict(title="% of days fleet is grounded (ground-day rate)", range=[0, 45],
                   showgrid=True, gridcolor="#e0e0e0"),
        yaxis=dict(title=""),
        showlegend=False,
    )

    as_of = df_gd["as_of_date"].max().strftime("%b %Y")
    fig.add_annotation(
        text=f"Source: Aviation Week Fleet Discovery / Tracked Aircraft Utilization, as of {as_of}",
        xref="paper", yref="paper", x=0, y=-0.18, showarrow=False,
        font=dict(size=10, color="#999"), xanchor="left",
    )

    print("  Built chart 5")
    return fig_to_div(fig)


 
# Chart 6 — A320neo vs A321neo variant split
 
def chart6() -> str:
    df_v = df_variant.copy()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_v["variant"],
        y=df_v["pct_parked_or_stored"],
        name="% parked or stored",
        marker_color=PALETTE["primary"],
        text=[f"{v:.0f}%" for v in df_v["pct_parked_or_stored"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Parked/stored: %{y:.0f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df_v["variant"],
        y=df_v["ground_day_pct_sep2025"],
        name="Ground-day % (Sep 2025)",
        marker_color=PALETTE["accent"],
        text=[f"{v:.0f}%" for v in df_v["ground_day_pct_sep2025"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Ground-day (Sep 2025): %{y:.0f}%<extra></extra>",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="A320neo vs A321neo: Variant-Level Grounding Severity", font=dict(size=15, color="#222")),
        xaxis=dict(title=""),
        yaxis=dict(title="%", range=[0, 60], showgrid=True, gridcolor="#e0e0e0"),
        barmode="group",
        legend=dict(x=0.65, y=0.99, bgcolor="rgba(255,255,255,0.85)", borderwidth=1),
    )

    as_of = df_v["as_of_date"].max().strftime("%b %Y")
    fig.add_annotation(
        text=f"Source: Aviation Week Fleet Discovery, as of {as_of}",
        xref="paper", yref="paper", x=0, y=-0.18, showarrow=False,
        font=dict(size=10, color="#999"), xanchor="left",
    )

    print("  Built chart 6")
    return fig_to_div(fig)


 
# Fleet Context Panel — grounded aircraft as share of global GTF fleet
 
def chart_fleet_context() -> str:
    grounded = int(latest_global["grounded_aircraft"])
    total_fleet = int(latest_global["total_gtf_fleet"])
    pct = latest_global["pct_grounded"]
    flying = total_fleet - grounded

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=["Global GTF Fleet"], x=[grounded], orientation="h",
        name=f"Grounded ({grounded:,})", marker_color=PALETTE["accent"],
        text=[f"{grounded:,} grounded ({pct:.1f}%)"], textposition="inside",
        insidetextanchor="middle", textfont=dict(color="white", size=14),
        hovertemplate=f"<b>Grounded</b><br>{grounded:,} aircraft ({pct:.1f}%)<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=["Global GTF Fleet"], x=[flying], orientation="h",
        name=f"Flying ({flying:,})", marker_color=PALETTE["muted"],
        text=[f"{flying:,} flying ({100-pct:.1f}%)"], textposition="inside",
        insidetextanchor="middle", textfont=dict(color="white", size=14),
        hovertemplate=f"<b>Flying</b><br>{flying:,} aircraft ({100-pct:.1f}%)<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT, barmode="stack",
        title=dict(text=f"{grounded:,} of {total_fleet:,} GTF-Powered Aircraft Are Grounded ({pct:.1f}% of the Global Fleet)",
                   font=dict(size=15, color="#222")),
        xaxis=dict(title="Aircraft", range=[0, total_fleet*1.02], showgrid=True, gridcolor="#e0e0e0"),
        yaxis=dict(title="", showticklabels=False),
        showlegend=True, legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.25),
        height=240,
    )
    print("  Built fleet context panel")
    return fig_to_div(fig)


def chart_fleet_breakdown() -> str:
    grounded = int(latest_global["grounded_aircraft"])
    latest_named = df_airlines.sort_values("date").groupby("airline", as_index=False).last()
    named_total = int(latest_named["grounded_aircraft"].sum())
    rest = grounded - named_total

    sorted_named = latest_named.sort_values("grounded_aircraft", ascending=False)
    labels = list(sorted_named["airline"]) + ["Rest of global fleet"]
    values = list(sorted_named["grounded_aircraft"]) + [rest]
    colors = [PALETTE["accent"], PALETTE["primary"], PALETTE["mid"], "#c9954f", "#8e6fb5"][:len(labels)-1] + [PALETTE["muted"]]

    fig = go.Figure(go.Bar(
        x=labels, y=values, marker_color=colors,
        text=[f"{v:,}" for v in values], textposition="outside",
        hovertemplate="<b>%{x}</b><br>Grounded: %{y:,}<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text=f"Where the {grounded:,} Grounded Aircraft Sit (Named Airlines vs Rest of Global Fleet)",
                   font=dict(size=15, color="#222")),
        xaxis=dict(title=""), yaxis=dict(title="Aircraft Grounded", showgrid=True, gridcolor="#e0e0e0"),
        showlegend=False,
    )
    print("  Built fleet breakdown chart")
    return fig_to_div(fig)


 
# Chart 7 — Emissions Penalty: extra CO2 from flying ceo instead of grounded GTF
 
FUEL_BURN_TPH = 2.5          # tonnes/hr, A320-family ceo total-aircraft cruise burn (sourced: airliners.net pilot/engineer consensus, 2.0-2.6 t/hr range)
DAILY_BLOCK_HOURS = 10.8     # MIT Airline Data Project, 2019 pre-pandemic avg, all sectors, US DOT Form 41
CO2_PER_KG_FUEL = 3.16       # IATA jet fuel CO2 conversion factor
PERIOD_DAYS = 18 * 30.44     # 18-month window
PERIOD_CO2_PER_AC = FUEL_BURN_TPH * DAILY_BLOCK_HOURS * PERIOD_DAYS * CO2_PER_KG_FUEL  # tonnes/aircraft over 18mo

PENALTY_LOW, PENALTY_MID, PENALTY_HIGH = 0.16, 0.175, 0.20   # sourced: reported GTF-vs-ceo fuel efficiency gap
FLEET_LOW, FLEET_HIGH = 687, 835

HEADLINE_CO2 = PERIOD_CO2_PER_AC * PENALTY_MID * FLEET_HIGH
LOW_CO2 = PERIOD_CO2_PER_AC * PENALTY_LOW * FLEET_LOW
HIGH_CO2 = PERIOD_CO2_PER_AC * PENALTY_HIGH * FLEET_HIGH


def chart7() -> str:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Low<br>(16% penalty, 687 a/c)", "Mid-case<br>(17.5% penalty, 835 a/c)", "High<br>(20% penalty, 835 a/c)"],
        y=[LOW_CO2/1e6, HEADLINE_CO2/1e6, HIGH_CO2/1e6],
        marker_color=[PALETTE["muted"], PALETTE["accent"], PALETTE["primary"]],
        text=[f"{v/1e6:.1f}M t" for v in [LOW_CO2, HEADLINE_CO2, HIGH_CO2]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Extra CO2: %{y:.2f}M tonnes<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text=f"Emissions Penalty: ~{HEADLINE_CO2/1e6:.1f}M Tonnes Extra CO2 Over 18 Months from Flying Older Aircraft Instead of Grounded GTF Jets",
                   font=dict(size=14, color="#222")),
        xaxis=dict(title=""),
        yaxis=dict(title="Extra CO2 (Million Tonnes)", range=[0, 9], showgrid=True, gridcolor="#e0e0e0"),
        showlegend=False,
        annotations=[dict(font=dict(color="#999", size=10), showarrow=False,
            text="Methodology: 2.5 t/hr ceo fuel burn x 10.8 daily block hrs (MIT ADP) x 3.16 kg CO2/kg fuel (IATA) x fuel-burn penalty x fleet size x 18 months. See sources.md.",
            x=0, xanchor="left", xref="paper", y=-0.22, yref="paper")],
    )
    print("  Built chart 7")
    return fig_to_div(fig)


 
# Chart 8 — CO2e Extension: non-CO2 climate multipliers applied to Chart 7
 
def chart8() -> str:
    scenarios = [
        ("Contrail-only<br>(Johansson et al. 2025)", 1.23),
        ("GWP100 contrail<br>(Lee et al. 2020/21)", 1.63),
        ("Industry RFI<br>rule-of-thumb (EASA)", 1.7),
    ]
    labels = [s[0] for s in scenarios]
    co2e_values = [HEADLINE_CO2 * s[1] / 1e6 for s in scenarios]
    multiplier_labels = [f"{s[1]:.2f}x" for s in scenarios]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=[HEADLINE_CO2/1e6]*3,
        name="CO2 (mid-case, from Chart 7)", marker_color=PALETTE["primary"],
        hovertemplate="<b>%{x}</b><br>Base CO2: %{y:.1f}M tonnes<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=labels, y=[v - HEADLINE_CO2/1e6 for v in co2e_values],
        name="Additional non-CO2 climate-equivalent", marker_color=PALETTE["accent"],
        text=multiplier_labels, textposition="outside",
        hovertemplate="<b>%{x}</b><br>Additional CO2e: %{y:.1f}M tonnes<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT, barmode="stack",
        title=dict(text=f"CO2e Extension: {co2e_values[0]:.1f}M-{co2e_values[2]:.1f}M Tonnes CO2-Equivalent Once Non-CO2 Climate Effects Are Included",
                   font=dict(size=14, color="#222")),
        xaxis=dict(title=""), yaxis=dict(title="CO2e (Million Tonnes)", showgrid=True, gridcolor="#e0e0e0"),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.18),
        annotations=[dict(font=dict(color="#999", size=10), showarrow=False,
            text="Multipliers apply to differing scopes (contrail-only vs. all non-CO2 effects) and time horizons, not directly comparable as a single range. Three named, sourced scenarios, not a confidence interval.",
            x=0, xanchor="left", xref="paper", y=-0.30, yref="paper")],
    )
    print("  Built chart 8")
    return fig_to_div(fig)


 
# Financial Lens — F1: Wizz Air disclosed P&W compensation
 
def chart_f1_compensation() -> str:
    comp_events = [("2024-05-27", 198.6, "FY2024 Annual Results"), ("2024-11-07", 146.0, "H1 FY2025 Results")]
    labels = [l for _, _, l in comp_events]
    values = [v for _, v, _ in comp_events]

    fig = go.Figure(go.Bar(
        x=labels, y=values, marker_color="#2e7d4f",
        text=[f"€{v:.1f}M" for v in values], textposition="outside",
        hovertemplate="<b>%{x}</b><br>P&W compensation: €%{y:.1f}M<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Wizz Air: Disclosed P&W Compensation Payments", font=dict(size=15, color="#222")),
        xaxis=dict(title=""), yaxis=dict(title="Compensation (€ Million)", showgrid=True, gridcolor="#e0e0e0"),
        showlegend=False,
        annotations=[dict(font=dict(color="#999", size=10), showarrow=False,
            text="Source: Wizz Air earnings calls, FY2024 and H1 FY2025 (data/wizz_air_comms.csv). Subsequent compensation deals (Jan 2025, Aug 2025) did not disclose specific amounts publicly.",
            x=0, xanchor="left", xref="paper", y=-0.22, yref="paper")],
    )
    print("  Built chart F1")
    return fig_to_div(fig)


def chart_f2_profit_miss() -> str:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Q1 FY2026 Operating Profit"], y=[87], name="Forecast", marker_color=PALETTE["muted"],
                          text=["€87M"], textposition="outside", hovertemplate="Forecast: €%{y}M<extra></extra>"))
    fig.add_trace(go.Bar(x=["Q1 FY2026 Operating Profit"], y=[27], name="Actual", marker_color=PALETTE["accent"],
                          text=["€27M"], textposition="outside", hovertemplate="Actual: €%{y}M<extra></extra>"))
    miss_pct = (1 - 27/87) * 100
    fig.update_layout(
        **BASE_LAYOUT, barmode="group",
        title=dict(text=f"Wizz Air Q1 FY2026: Operating Profit Missed Forecast by {miss_pct:.0f}%", font=dict(size=15, color="#222")),
        xaxis=dict(title=""), yaxis=dict(title="Operating Profit (€ Million)", showgrid=True, gridcolor="#e0e0e0"),
        legend=dict(x=0.75, y=0.99, bgcolor="rgba(255,255,255,0.85)", borderwidth=1),
        annotations=[dict(font=dict(color="#999", size=10), showarrow=False,
            text="Source: Wizz Air Q1 FY2026 earnings call, 24 Jul 2025 (data/wizz_air_comms.csv). Company attributed the miss substantially to GTF grounding-related costs and lost capacity.",
            x=0, xanchor="left", xref="paper", y=-0.22, yref="paper")],
    )
    print("  Built chart F2")
    return fig_to_div(fig)


def chart_f3_engine_economics() -> str:
    fig = go.Figure(go.Bar(
        x=["Single engine<br>(per month)", "Engine pair<br>(per month)", "Engine pair<br>(annualized)"],
        y=[200_000, 400_000, 4_800_000],
        marker_color=[PALETTE["muted"], "#2e7d4f", PALETTE["accent"]],
        text=["$200K/mo", "$400K/mo", "$4.8M/yr"], textposition="outside",
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Why Parting Out a Young Aircraft Can Beat Flying It: GTF Spare Engine Lease Rates", font=dict(size=14, color="#222")),
        xaxis=dict(title=""), yaxis=dict(title="USD", showgrid=True, gridcolor="#e0e0e0", tickformat="$,.0f"),
        showlegend=False,
        annotations=[dict(font=dict(color="#999", size=10), showarrow=False,
            text="Source: Cirium data, widely reported (Reuters/Simple Flying/AirInsight, 2025-2026) — a GTF engine pair leased as spares can generate revenue comparable to leasing the whole aircraft, incentivizing part-out over repair-and-fly.",
            x=0, xanchor="left", xref="paper", y=-0.24, yref="paper")],
    )
    print("  Built chart F3")
    return fig_to_div(fig)


def chart_f4_industry_cost() -> str:
    fig = go.Figure(go.Bar(
        x=["Total supply-chain<br>disruption cost", "Of which:<br>engine-related costs"],
        y=[11, 2.6], marker_color=[PALETTE["primary"], PALETTE["accent"]],
        text=["$11B", "$2.6B"], textposition="outside",
        hovertemplate="<b>%{x}</b><br>$%{y}B<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="IATA Estimate: Industry-Wide Cost of Supply Chain Disruption", font=dict(size=15, color="#222")),
        xaxis=dict(title=""), yaxis=dict(title="USD Billion", showgrid=True, gridcolor="#e0e0e0"),
        showlegend=False,
        annotations=[dict(font=dict(color="#999", size=10), showarrow=False,
            text="Source: IATA Director General Willie Walsh, cited across multiple outlets (AviTrader, AeroMorning, 2025) — covers industry-wide supply chain and maintenance delay costs, not GTF-specific alone, though GTF is cited as a major contributor.",
            x=0, xanchor="left", xref="paper", y=-0.22, yref="paper")],
    )
    print("  Built chart F4")
    return fig_to_div(fig)


 
# Structural vs. Bridge — written takeaway (Charts 5 & 6 context)
 
def structural_vs_bridge_section() -> str:
    mro_latest = 139  # P&W internal MRO output index, 2024 = 100 (see chart3 mro_data)
    mro_growth_pct = mro_latest - 100
    gtf_ground_day = df_ground_day.loc[df_ground_day["engine_family"].str.contains("PW1000G"), "ground_day_pct_low"].iloc[0]
    leap_low, leap_high = df_ground_day.loc[df_ground_day["engine_family"] == "CFM Leap", ["ground_day_pct_low", "ground_day_pct_high"]].iloc[0]
    legacy_low, legacy_high = df_ground_day.loc[df_ground_day["engine_family"].str.contains("legacy"), ["ground_day_pct_low", "ground_day_pct_high"]].iloc[0]
    a320_pct = df_variant.loc[df_variant["variant"].str.contains("A320neo"), "pct_parked_or_stored"].iloc[0]
    a321_pct = df_variant.loc[df_variant["variant"].str.contains("A321neo"), "pct_parked_or_stored"].iloc[0]

    return f"""
  <div class="chart-section takeaway-section">
    <h2>Reading Charts 5 &amp; 6: Structural Backlog, Not a Short Bridge</h2>
    <div class="summary-box" style="border-color:#1a6fb5">
      <p>
        P&amp;W's own MRO output index rose from a baseline of 100 to roughly {mro_latest}
        (+{mro_growth_pct}%) by late 2025 — genuine progress, and worth taking at face value.
        But a {mro_growth_pct}% throughput improvement against a backlog this large is a rate of
        clearance, not a resolution date, and it has to be read against the fleet's actual
        availability: the GTF-powered fleet's ground-day rate sits around {gtf_ground_day:.0f}%,
        well above the {leap_low:.0f}–{leap_high:.0f}% rate of its closest rival (CFM Leap) and even
        above the {legacy_low:.0f}–{legacy_high:.0f}% rate of the older, more maintenance-hungry
        engines (CFM56, V2500) that GTF-powered aircraft were meant to retire.
      </p>
      <p>
        That comparison is the tell. An engine family running less available than the aircraft it
        replaces, more than two years into a stated three-year inspection programme, points to a
        multi-year structural backlog rather than a bridge that clears on its own. The variant split
        sharpens this further: A320neo aircraft — the bulk of the affected fleet — show
        {a320_pct:.0f}% parked or stored, against {a321_pct:.0f}% for the A321neo. Recovery is not
        running at one uniform pace across the fleet; it is uneven by variant, which argues against
        treating the backlog as a single countdown with one end date.
      </p>
      <p>
        <strong>Working assumption:</strong> the emissions penalty calculated elsewhere in this
        project should be modelled as a multi-year structural cost, not a short-term bridge that
        resolves cleanly once MRO throughput catches up. Conservative scenarios should still allow
        for the possibility that this assumption is wrong in the airlines' favour — but nothing in
        the public data available as of this writing supports betting on a fast resolution.
      </p>
    </div>
  </div>"""


 
# Wizz Air Narrative vs Reality — HTML section
 
def _nearest_grounding(target_date: pd.Timestamp) -> str:
    """Return grounded count for the Wizz Air data point closest to target_date."""
    if df_wizz.empty:
        return "n/a"
    idx = (df_wizz["date"] - target_date).abs().idxmin()
    row = df_wizz.loc[idx]
    days_diff = abs((row["date"] - target_date).days)
    count = int(row["grounded_aircraft"])
    if days_diff > 120:
        return f"{count} ⚠️ ({row['date'].strftime('%b %Y')} data)"
    return str(count)


def wizz_narrative_section() -> str:
    # ── Timeline table ────────────────────────────────────────────────────
    rows_html = []
    for _, row in df_comms.iterrows():
        score = int(row["sentiment_score"])
        badge_color = SENTIMENT_COLOR.get(score, "#888")
        badge_label = SENTIMENT_LABEL.get(score, "")
        actual = _nearest_grounding(row["date"])
        src_label = row["source_type"].replace("_", " ").title()
        url = row["url"]
        rows_html.append(f"""
        <tr>
          <td style="white-space:nowrap">{row['date'].strftime('%b %Y')}</td>
          <td><span class="src-badge">{src_label}</span></td>
          <td><a href="{url}" target="_blank" rel="noopener">{row['headline']}</a></td>
          <td style="font-size:0.85rem;color:#555">{row['key_claim']}</td>
          <td style="text-align:center;font-weight:700">{actual}</td>
          <td><span class="sentiment-badge" style="background:{badge_color}">{badge_label}</span></td>
        </tr>""")
    timeline_table = "\n".join(rows_html)

    # ── Slippage analysis ─────────────────────────────────────────────────
    slippage_items = [
        ("May 2024", "End of calendar 2026", "Initial P&W compensation agreement horizon"),
        ("Nov 2024", "F27 (≈ Mar 2027)", "H1 FY2025 results — quietly pushed 3 months"),
        ("Jun 2025", "End of calendar 2027", "FY2025 annual results — full 12-month slip acknowledged"),
        ("Jul 2025", "March 2027", "Q1 FY2026 results — reiterated, no improvement"),
        ("Jan 2026", "End of calendar 2027", "Q3 FY2026 — P&W compensation now extended to match"),
    ]
    slippage_rows = "\n".join(
        f"<tr><td>{d}</td><td>{t}</td><td>{n}</td></tr>"
        for d, t, n in slippage_items
    )

    # ── Sentiment trend ───────────────────────────────────────────────────
    scores = df_comms["sentiment_score"].tolist()
    dates  = [d.strftime("%b %Y") for d in df_comms["date"]]
    avg    = sum(scores) / len(scores)
    trend_direction = "slightly more pessimistic" if scores[-1] < scores[0] else "broadly stable"
    trend_items = "".join(
        f'<div class="sent-pip" style="background:{SENTIMENT_COLOR[s]}" title="{dates[i]}: {SENTIMENT_LABEL[s]}"></div>'
        for i, s in enumerate(scores)
    )

    return f"""
  <div class="chart-section wizz-section">
    <h2>Wizz Air: Public Narrative vs Reality</h2>

    <div class="summary-box" style="border-color:#e85d26">
      <p>
        Wizz Air is the world's largest operator of Pratt &amp; Whitney GTF-powered aircraft and
        has been one of the hardest-hit airlines in the engine crisis. This section tracks their
        public statements — earnings calls, press releases, and CEO interviews — and compares them
        against the actual grounding numbers on or near those same dates.
        <br><br>
        <strong>Key finding:</strong> Wizz Air's stated resolution timeline has slipped by at least
        <strong>12 months</strong> (from end-2026 to end-2027), while language in public
        communications turned noticeably more pessimistic through late 2025 before stabilising
        as grounding counts finally began to fall.
        <br><br>
        <em>Note: Data before May 2024 is a gap — Wizz Air did not disclose specific grounded-aircraft
        counts in public statements prior to their FY2024 annual results.</em>
      </p>
    </div>

    <h3 style="font-size:1rem;margin:24px 0 10px;color:#444">Communications Timeline vs Actual Grounding Count</h3>
    <div style="overflow-x:auto">
      <table class="wizz-table">
        <thead>
          <tr>
            <th>Date</th><th>Type</th><th>Headline / Source</th>
            <th>Key Claim</th><th>Actual Grounded</th><th>Sentiment</th>
          </tr>
        </thead>
        <tbody>
{timeline_table}
        </tbody>
      </table>
    </div>
    <p class="table-note">⚠️ flag = nearest available data point is &gt;120 days from statement date.</p>

    <h3 style="font-size:1rem;margin:28px 0 10px;color:#444">Timeline Slippage</h3>
    <p style="font-size:0.9rem;color:#555;margin-bottom:10px">
      Each time Wizz Air updated its forward guidance, the target resolution date moved further out.
    </p>
    <table class="wizz-table">
      <thead><tr><th>Statement Date</th><th>Claimed Resolution</th><th>Context</th></tr></thead>
      <tbody>{slippage_rows}</tbody>
    </table>

    <h3 style="font-size:1rem;margin:28px 0 8px;color:#444">Sentiment Tracker</h3>
    <p style="font-size:0.9rem;color:#555;margin-bottom:10px">
      Each pip represents one public communication, chronologically left-to-right.
      Overall trend is <strong>{trend_direction}</strong>
      (average score {avg:.1f}/5 where 1 = Very Pessimistic, 5 = Very Optimistic).
    </p>
    <div class="sent-row">{trend_items}</div>
    <div class="sent-legend">
      {"".join(f'<span><span class="sent-pip" style="background:{c};display:inline-block"></span> {l}</span>' for c, l in zip(SENTIMENT_COLOR.values(), SENTIMENT_LABEL.values()))}
    </div>
  </div>"""


 
# Generate chart HTML snippets
 
print("Generating charts …")
div_chart1 = chart1()
div_chart2 = chart2()
div_chart3 = chart3()
div_chart4 = chart4()
div_chart5 = chart5()
div_chart6 = chart6()
div_fleet_context = chart_fleet_context()
div_fleet_breakdown = chart_fleet_breakdown()
div_chart7 = chart7()
div_chart8 = chart8()
div_f1 = chart_f1_compensation()
div_f2 = chart_f2_profit_miss()
div_f3 = chart_f3_engine_economics()
div_f4 = chart_f4_industry_cost()
div_wizz_narrative = wizz_narrative_section()
div_structural_takeaway = structural_vs_bridge_section()


 
# Plain-English summary
 
latest_global  = df_global.sort_values("date").iloc[-1]
first_global   = df_global.sort_values("date").iloc[0]
delta          = int(latest_global["grounded_aircraft"]) - int(first_global["grounded_aircraft"])
last_updated   = df["date"].max().strftime("%B %d, %Y").lstrip("0")
latest_date_str = latest_global["date"].strftime("%B %Y")
worst_airline  = (
    df_airlines.sort_values("date").groupby("airline").last()
    .sort_values("pct_grounded", ascending=False).iloc[0]
)

summary = (
    f"As of {latest_date_str}, <strong>{int(latest_global['grounded_aircraft'])} GTF-powered aircraft</strong> "
    f"({latest_global['pct_grounded']:.1f}% of the global GTF fleet) remain on the ground awaiting "
    f"Pratt &amp; Whitney PW1000G engine inspections or repair — up from "
    f"{int(first_global['grounded_aircraft'])} ({first_global['pct_grounded']:.1f}%) in "
    f"{first_global['date'].strftime('%B %Y')}, a net increase of {delta} aircraft. "
    f"At the airline level, <strong>{worst_airline.name}</strong> is the hardest hit with "
    f"{worst_airline['pct_grounded']:.1f}% of its GTF fleet grounded. "
    f"On the supply-chain side, P&amp;W MRO throughput has improved — the internal output index "
    f"rose from 100 in 2024 to an estimated 139 by Q4 2025 — yet the grounded count continues "
    f"to climb, reflecting ongoing delivery of new aircraft that themselves require inspection "
    f"before entering service. The data suggests the crisis is not yet over."
)


 
# Sources
 
SOURCES = [
    ("FlightGlobal / Cirium", "Fleet data and grounding counts, various dates 2024–2025"),
    ("RTX / Pratt &amp; Whitney Earnings Calls", "MRO output index and JetBlue fleet data (Q1 2025, Q1 2026)"),
    ("FlightGlobal", "Wizz Air, Volaris, VivaAerobus airline-level grounding figures"),
    ("Wizz Air Earnings Calls (FY2024–Q3 FY2026)", "Wizz Air grounded-aircraft counts and forward guidance — see <code>data/wizz_air_comms.csv</code> for full citation list"),
    ("Simple Flying / Aerotime / ch-aviation", "Wizz Air GTF communications tracking; interview quotes from CEO József Váradi and CFO Ian Malin"),
    ("Wizz Air RNS / SEC Filings", "FY2025 Annual Results (5 Jun 2025); Q1 FY2026 Results (24 Jul 2025)"),
    ("Aviation Week Fleet Discovery / Tracked Aircraft Utilization", "Ground-day rate comparison (Chart 5) and A320neo/A321neo variant split (Chart 6), as of 20 Oct 2025 — note: uses a ≥30-day grounding threshold, a different methodology from the FlightGlobal/Cirium-based charts above"),
    ("MIT Airline Data Project (US DOT Form 41)", "Daily block-hour utilization baseline (10.8 hrs/day, 2019), used in Chart 7 emissions methodology"),
    ("IATA", "Jet fuel CO2 conversion factor (3.16 kg CO2/kg fuel), used in Chart 7"),
    ("Johansson et al. 2025; Lee et al. 2020/21 (Atmospheric Environment 244); EASA non-CO2 climate impacts report", "Non-CO2 climate multipliers used in Chart 8 — see sources.md for full methodology and caveats"),
    ("Cirium (via Reuters / Simple Flying / AirInsight, 2025–2026)", "GTF spare engine lease rates (~$200K/month/engine), used in Financial Lens Chart F3"),
    ("IATA Director General Willie Walsh (via AviTrader / AeroMorning, 2025)", "Industry-wide supply chain disruption cost estimate ($11B total, $2.6B engine-related), used in Financial Lens Chart F4"),
]


sources_rows = "\n".join(
    f"<tr><td>{s}</td><td>{d}</td></tr>" for s, d in SOURCES
)


 
# HTML report
 
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GTF Grounding Tracker</title>
<script charset="utf-8" src="https://cdn.plot.ly/plotly-3.6.0.min.js" integrity="sha256-QaOVwtVY0T02VaHrr6pnoHLCwayMJp4O5n4YyaE3rJk=" crossorigin="anonymous"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #f0f4f8;
    color: #222;
    line-height: 1.65;
  }}
  .container {{ max-width: 980px; margin: 0 auto; padding: 36px 24px 64px; }}
  header {{ margin-bottom: 36px; border-bottom: 3px solid #1a6fb5; padding-bottom: 20px; }}
  header h1 {{ font-size: 2rem; color: #1a6fb5; letter-spacing: -0.5px; }}
  header .subtitle {{ font-size: 1.05rem; color: #555; margin-top: 6px; }}
  .meta {{ font-size: 0.85rem; color: #888; margin-top: 8px; }}
  .summary-box {{
    background: #fff;
    border-left: 4px solid #1a6fb5;
    border-radius: 6px;
    padding: 18px 22px;
    margin-bottom: 36px;
    font-size: 0.97rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  .chart-section {{ margin-bottom: 40px; }}
  .chart-section h2 {{
    font-size: 1.1rem;
    color: #333;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #ddd;
  }}
  .chart-section .plotly-chart {{
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    background: #f7f9fc;
    overflow: hidden;
  }}
  .sources-section {{ margin-top: 48px; }}
  .sources-section h2 {{ font-size: 1.1rem; color: #333; margin-bottom: 14px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 10px 14px; border-bottom: 1px solid #e4e8ee; }}
  th {{ background: #e8f0fa; color: #1a6fb5; font-weight: 600; }}
  tr:last-child td {{ border-bottom: none; }}
  footer {{ margin-top: 48px; font-size: 0.8rem; color: #aaa; text-align: center; }}
  .takeaway-section {{ border-top: 3px solid #1a6fb5; padding-top: 24px; margin-top: 48px; }}
  .wizz-section {{ border-top: 3px solid #e85d26; padding-top: 24px; margin-top: 48px; }}
  .wizz-section h2 {{ color: #e85d26; }}
  .wizz-table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-bottom: 6px; }}
  .wizz-table th, .wizz-table td {{ text-align: left; padding: 9px 12px; border-bottom: 1px solid #e4e8ee; vertical-align: top; }}
  .wizz-table th {{ background: #fff3ee; color: #c0440f; font-weight: 600; }}
  .wizz-table tr:hover td {{ background: #fffaf7; }}
  .src-badge {{ background: #e8f0fa; color: #1a6fb5; font-size: 0.78rem; padding: 2px 7px; border-radius: 10px; white-space: nowrap; }}
  .sentiment-badge {{ color: #fff; font-size: 0.78rem; padding: 2px 8px; border-radius: 10px; white-space: nowrap; }}
  .sent-row {{ display: flex; gap: 6px; margin: 6px 0 10px; flex-wrap: wrap; }}
  .sent-pip {{ width: 28px; height: 28px; border-radius: 50%; display: inline-block; cursor: default; }}
  .sent-legend {{ display: flex; gap: 16px; flex-wrap: wrap; font-size: 0.82rem; color: #555; margin-top: 4px; align-items: center; }}
  .sent-legend span {{ display: flex; align-items: center; gap: 5px; }}
  .table-note {{ font-size: 0.8rem; color: #888; margin-top: 4px; }}

  /* Lens tabs */
  .lens-intro {{ margin: 8px 0 28px; font-size: 0.95rem; color: #555; }}
  .lens-tabs {{ display: flex; gap: 8px; margin-bottom: 28px; border-bottom: 2px solid #ddd; }}
  .lens-tab {{
    padding: 12px 22px; font-size: 0.98rem; font-weight: 600; cursor: pointer;
    background: none; border: none; color: #888;
    border-bottom: 3px solid transparent; margin-bottom: -2px;
    transition: color 0.15s, border-color 0.15s;
  }}
  .lens-tab:hover {{ color: #333; }}
  .lens-tab.active.financial {{ color: #2e7d4f; border-bottom-color: #2e7d4f; }}
  .lens-tab.active.climate {{ color: #1a6fb5; border-bottom-color: #1a6fb5; }}
  .lens-panel {{ display: none; }}
  .lens-panel.active {{ display: block; }}
  .lens-panel-intro {{
    background: #fff; border-radius: 6px; padding: 16px 20px; margin-bottom: 28px;
    font-size: 0.95rem; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  .lens-panel-intro.financial {{ border-left: 4px solid #2e7d4f; }}
  .lens-panel-intro.climate {{ border-left: 4px solid #1a6fb5; }}
  .overview-divider {{ margin: 48px 0 32px; padding-top: 24px; border-top: 3px solid #333; }}
  .overview-divider h2 {{ font-size: 1.3rem; color: #222; margin-bottom: 6px; }}
  .overview-divider p {{ font-size: 0.92rem; color: #666; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>GTF Grounding Tracker</h1>
    <p class="subtitle">Tracking the Pratt &amp; Whitney GTF crisis — supply chain drag, fleet impact, and recovery signals</p>
    <p class="meta">Last updated: {last_updated}</p>
  </header>

  <div class="summary-box">
    <p>{summary}</p>
  </div>

  <div class="chart-section">
    <h2>Fleet Context — Grounded Aircraft as Share of the Global GTF Fleet</h2>
    <div class="plotly-chart">
      {div_fleet_context}
    </div>
  </div>

  <div class="chart-section">
    <h2>Fleet Context — Where the Grounded Aircraft Sit</h2>
    <div class="plotly-chart">
      {div_fleet_breakdown}
    </div>
    <p style="font-size:0.85rem;color:#888;margin-top:8px;">
      Named airlines with publicly disclosed grounded-aircraft counts (Wizz Air, Volaris, VivaAerobus, JetBlue) account for a small share of the global total. The remainder reflects aircraft grounded at airlines without individually disclosed, sourced figures in this dataset, not aircraft outside the GTF fleet.
    </p>
  </div>

  <div class="chart-section">
    <h2>Chart 1 — Global Grounding Trend</h2>
    <div class="plotly-chart">
      {div_chart1}
    </div>
  </div>

  <div class="chart-section">
    <h2>Chart 2 — Most Affected Airlines</h2>
    <div class="plotly-chart">
      {div_chart2}
    </div>
  </div>

  <div class="chart-section">
    <h2>Chart 3 — Groundings vs MRO Recovery</h2>
    <div class="plotly-chart">
      {div_chart3}
    </div>
  </div>

  <div class="chart-section">
    <h2>Chart 4 — Wizz Air: Grounding Trajectory vs PR Moments</h2>
    <div class="plotly-chart">
      {div_chart4}
    </div>
  </div>

  <div class="chart-section">
    <h2>Chart 5 — Ground-Day Rate: GTF vs Competing Engines</h2>
    <div class="plotly-chart">
      {div_chart5}
    </div>
  </div>

  <div class="chart-section">
    <h2>Chart 6 — A320neo vs A321neo Variant Split</h2>
    <div class="plotly-chart">
      {div_chart6}
    </div>
  </div>

  {div_structural_takeaway}

  <div class="overview-divider">
    <h2>Two Ways to Read This Crisis</h2>
    <p>The groundings above create two distinct, quantifiable exposures: a financial one (compensation, lost revenue, distorted asset values) and a climate one (extra emissions from flying older aircraft instead). Pick a lens below — each draws on different sourced data to answer a different question.</p>
  </div>

  <div class="lens-tabs">
    <button class="lens-tab financial active" id="tab-financial" onclick="showLens('financial')">💰 Financial Lens</button>
    <button class="lens-tab climate" id="tab-climate" onclick="showLens('climate')">🌍 Climate Lens</button>
  </div>

  <div class="lens-panel active" id="panel-financial">
    <div class="lens-panel-intro financial">
      <p><strong>The financial question:</strong> what is the GTF crisis actually costing airlines, lessors, and the wider industry — and where is value flowing instead? Drawing on disclosed compensation payments, profit misses, and the spare-engine market.</p>
    </div>

    <div class="chart-section">
      <h2>F1 — Wizz Air: Disclosed P&amp;W Compensation</h2>
      <div class="plotly-chart">
        {div_f1}
      </div>
    </div>

    <div class="chart-section">
      <h2>F2 — Wizz Air: Operating Profit Miss</h2>
      <div class="plotly-chart">
        {div_f2}
      </div>
    </div>

    <div class="chart-section">
      <h2>F3 — Spare Engine Lease Economics</h2>
      <div class="plotly-chart">
        {div_f3}
      </div>
    </div>

    <div class="chart-section">
      <h2>F4 — Industry-Wide Cost Estimate</h2>
      <div class="plotly-chart">
        {div_f4}
      </div>
    </div>
  </div>

  <div class="lens-panel" id="panel-climate">
    <div class="lens-panel-intro climate">
      <p><strong>The climate question:</strong> what does it cost the planet when 835 fuel-efficient GTF aircraft sit grounded while airlines fly older, thirstier aircraft in their place? Drawing on sourced fuel-burn, utilization, and non-CO2 climate-effect data.</p>
    </div>

    <div class="chart-section">
      <h2>Chart 7 — Emissions Penalty: 18-Month Extra CO2 from Flying Older Aircraft</h2>
      <div class="plotly-chart">
        {div_chart7}
      </div>
    </div>

    <div class="chart-section">
      <h2>Chart 8 — CO2e Extension: Non-CO2 Climate Effects</h2>
      <div class="plotly-chart">
        {div_chart8}
      </div>
    </div>
  </div>

  {div_wizz_narrative}

  <div class="sources-section">
    <h2>Data Sources</h2>
    <table>
      <thead><tr><th>Source</th><th>Coverage</th></tr></thead>
      <tbody>
        {sources_rows}
      </tbody>
    </table>
  </div>

  <footer>
    <p>Data is updated manually. See <code>data/grounding_counts.csv</code> to add new entries.</p>
  </footer>
</div>
<script>
function showLens(lens) {{
  document.querySelectorAll('.lens-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.lens-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('panel-' + lens).classList.add('active');
  document.getElementById('tab-' + lens).classList.add('active');
}}
</script>
</body>
</html>
"""

print("Writing report …")
REPORT_FILE.write_text(html, encoding="utf-8")
print(f"  Saved {REPORT_FILE.relative_to(ROOT)}")
print()
print("Done. Open index.html to view the report.")
