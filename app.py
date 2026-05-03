"""
IMDB Top 1000 Movies Dashboard
BAN-461 Capstone Assignment
Analytical Question: Which movie genres earn the highest ratings and box office revenue,
and has that changed over the decades?
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ─────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="IMDB Top 1000 Analytics",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS STYLING — White background, dark readable text
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Professional color palette: white background, navy text, gold accent */
    .stApp {
        background-color: #FFFFFF;
        color: #1A1A2E;
    }

    .main { background-color: #FFFFFF; }

    /* Title block */
    .dashboard-title {
        font-family: 'Georgia', serif;
        font-size: 2.4rem;
        font-weight: 700;
        color: #1A1A2E;
        letter-spacing: 1px;
        margin-bottom: 0.2rem;
    }

    .dashboard-subtitle {
        font-size: 1rem;
        color: #4A4A6A;
        margin-bottom: 1.5rem;
        font-style: italic;
    }

    .analytical-question {
        background-color: #F0F4F8;
        border-left: 4px solid #B8860B;
        padding: 1rem 1.4rem;
        border-radius: 6px;
        margin-bottom: 1.5rem;
        font-size: 1.05rem;
        color: #1A1A2E;
    }

    /* KPI metric cards */
    [data-testid="metric-container"] {
        background-color: #F7F9FC;
        border: 1px solid #D0D8E4;
        border-top: 3px solid #B8860B;
        border-radius: 8px;
        padding: 1rem;
    }

    [data-testid="metric-container"] label {
        color: #4A4A6A !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    [data-testid="stMetricValue"] {
        color: #1A1A2E !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.85rem !important;
    }

    /* Section headers */
    .section-header {
        font-family: 'Georgia', serif;
        font-size: 1.3rem;
        color: #1A1A2E;
        border-bottom: 2px solid #B8860B;
        padding-bottom: 0.4rem;
        margin: 1.5rem 0 1rem 0;
    }

    /* Insight bullets */
    .insight-box {
        background-color: #F7F9FC;
        border-left: 3px solid #B8860B;
        padding: 0.8rem 1.2rem;
        border-radius: 0 6px 6px 0;
        margin: 0.5rem 0;
        color: #1A1A2E;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F0F4F8;
        border-right: 1px solid #D0D8E4;
    }

    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #1A1A2E !important;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid #D0D8E4;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA LOADING AND CLEANING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("imdb_top_1000.csv")

    # Clean Runtime: extract numeric minutes
    df["Runtime_Min"] = df["Runtime"].str.extract(r"(\d+)").astype(float)

    # Clean Gross: remove commas, convert to numeric
    df["Gross_USD"] = pd.to_numeric(
        df["Gross"].str.replace(",", "", regex=False), errors="coerce"
    )

    # Clean Released_Year: remove non-numeric rows (e.g., 'PG')
    df["Year"] = pd.to_numeric(df["Released_Year"], errors="coerce")
    df = df.dropna(subset=["Year"])
    df["Year"] = df["Year"].astype(int)

    # Create decade column for grouping
    df["Decade"] = (df["Year"] // 10 * 10).astype(str) + "s"

    # Extract primary genre (first listed)
    df["Primary_Genre"] = df["Genre"].str.split(",").str[0].str.strip()

    return df


df_raw = load_data()


# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
st.sidebar.markdown("## Filters")
st.sidebar.markdown("---")

# Filter 1: Decade range slider
min_year = int(df_raw["Year"].min())
max_year = int(df_raw["Year"].max())

year_range = st.sidebar.slider(
    "Release Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(1970, max_year),
    step=1,
)

# Filter 2: Primary genre multiselect
all_genres = sorted(df_raw["Primary_Genre"].dropna().unique())
selected_genres = st.sidebar.multiselect(
    "Primary Genre",
    options=all_genres,
    default=["Drama", "Action", "Comedy", "Crime", "Biography", "Animation", "Thriller"],
)

# Filter 3: Minimum IMDB rating slider
min_rating = st.sidebar.slider(
    "Minimum IMDB Rating",
    min_value=7.6,
    max_value=9.3,
    value=7.6,
    step=0.1,
    format="%.1f",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<span style='color:#4A4A6A; font-size:0.8rem;'>IMDB Top 1000 Dataset · BAN-461 Capstone</span>",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
df_filtered = df_raw[
    (df_raw["Year"] >= year_range[0])
    & (df_raw["Year"] <= year_range[1])
    & (df_raw["Primary_Genre"].isin(selected_genres) if selected_genres else True)
    & (df_raw["IMDB_Rating"] >= min_rating)
].copy()


# ─────────────────────────────────────────────
# DASHBOARD HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="dashboard-title">IMDB Top 1000 — Cinema Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">BAN-461 Capstone · Advanced Data Modeling Systems</div>', unsafe_allow_html=True)

st.markdown("""
<div class="analytical-question">
    <strong>Analytical Question:</strong> Which movie genres earn the highest audience ratings
    and box office revenue, and has that changed over the decades?
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# KPI METRICS
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">Key Performance Indicators</div>', unsafe_allow_html=True)

# Compute KPIs on filtered data vs. full dataset for deltas
avg_rating_filtered = df_filtered["IMDB_Rating"].mean()
avg_rating_all = df_raw["IMDB_Rating"].mean()
rating_delta = avg_rating_filtered - avg_rating_all

avg_gross_filtered = df_filtered["Gross_USD"].dropna().mean() / 1_000_000
avg_gross_all = df_raw["Gross_USD"].dropna().mean() / 1_000_000
gross_delta = avg_gross_filtered - avg_gross_all

top_genre = (
    df_filtered["Primary_Genre"].value_counts().idxmax()
    if not df_filtered.empty
    else "N/A"
)
top_genre_count = (
    df_filtered["Primary_Genre"].value_counts().max()
    if not df_filtered.empty
    else 0
)
total_films = len(df_filtered)
top_genre_pct = (top_genre_count / total_films * 100) if total_films > 0 else 0

avg_metascore_filtered = df_filtered["Meta_score"].dropna().mean()
avg_metascore_all = df_raw["Meta_score"].dropna().mean()
meta_delta = avg_metascore_filtered - avg_metascore_all

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Films in Selection",
    value=f"{total_films:,}",
    delta=f"{total_films - len(df_raw):+,} vs. full dataset",
)

col2.metric(
    label="Avg IMDB Rating",
    value=f"{avg_rating_filtered:.2f}" if not df_filtered.empty else "N/A",
    delta=f"{rating_delta:+.2f} vs. all films",
)

col3.metric(
    label="Avg Box Office Gross",
    value=f"${avg_gross_filtered:.1f}M" if not df_filtered.empty else "N/A",
    delta=f"${gross_delta:+.1f}M vs. all films",
)

col4.metric(
    label="Avg Metacritic Score",
    value=f"{avg_metascore_filtered:.0f}" if not df_filtered.empty else "N/A",
    delta=f"{meta_delta:+.1f} vs. all films",
)


# ─────────────────────────────────────────────
# CHART 1: Avg IMDB Rating by Primary Genre (Bar Chart)
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">Visualizations</div>', unsafe_allow_html=True)

# Professional color palette for charts — works on white background
CHART_COLORS = [
    "#1A4A7A", "#B8860B", "#7B2D8B", "#C0392B", "#1A6B3C",
    "#0E6B8C", "#D4520A", "#2C3E50", "#6B4226", "#4A235A"
]

col_left, col_right = st.columns(2)

with col_left:
    # CHART 1: Dual-axis grouped bar — Avg IMDB Rating AND Avg Gross by Genre
    genre_summary = (
        df_filtered.groupby("Primary_Genre")
        .agg(
            Avg_Rating=("IMDB_Rating", "mean"),
            Avg_Gross=("Gross_USD", "mean"),
        )
        .reset_index()
        .dropna(subset=["Avg_Gross"])
        .sort_values("Avg_Rating", ascending=False)
        .head(12)
    )
    genre_summary["Avg_Gross_M"] = genre_summary["Avg_Gross"] / 1_000_000

    fig_dual = go.Figure()

    # Bar 1: Avg IMDB Rating — left y-axis
    fig_dual.add_trace(go.Bar(
        name="Avg IMDB Rating",
        x=genre_summary["Primary_Genre"],
        y=genre_summary["Avg_Rating"],
        yaxis="y1",
        marker_color="#1A4A7A",
        text=genre_summary["Avg_Rating"].round(2),
        texttemplate="%{text:.2f}",
        textposition="outside",
        textfont=dict(color="#1A1A2E", size=10),
        offsetgroup=1,
    ))

    # Bar 2: Avg Box Office Gross — right y-axis
    fig_dual.add_trace(go.Bar(
        name="Avg Gross ($M)",
        x=genre_summary["Primary_Genre"],
        y=genre_summary["Avg_Gross_M"],
        yaxis="y2",
        marker_color="#B8860B",
        text=genre_summary["Avg_Gross_M"].round(0),
        texttemplate="$%{text:.0f}M",
        textposition="outside",
        textfont=dict(color="#1A1A2E", size=10),
        offsetgroup=2,
    ))

    fig_dual.update_layout(
        title="Avg IMDB Rating & Avg Box Office Gross by Genre",
        barmode="group",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font_color="#1A1A2E",
        title_font_color="#1A1A2E",
        xaxis=dict(
            tickangle=-30,
            gridcolor="#E0E0E0",
            linecolor="#CCCCCC",
            tickfont=dict(color="#1A1A2E"),
        ),
        yaxis=dict(
            title="Avg IMDB Rating",
            range=[7.0, 9.8],
            gridcolor="#E0E0E0",
            tickfont=dict(color="#1A4A7A"),
            title_font=dict(color="#1A4A7A"),
        ),
        yaxis2=dict(
            title="Avg Box Office Gross ($M)",
            overlaying="y",
            side="right",
            showgrid=False,
            tickfont=dict(color="#B8860B"),
            title_font=dict(color="#B8860B"),
        ),
        legend=dict(
            bgcolor="#F7F9FC",
            bordercolor="#D0D8E4",
            font=dict(color="#1A1A2E"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(t=70, b=70),
    )
    st.plotly_chart(fig_dual, use_container_width=True)

with col_right:
    # CHART 2: Average Gross by Decade (Line Chart)
    decade_data = (
        df_filtered.dropna(subset=["Gross_USD"])
        .groupby("Decade")
        .agg(
            Avg_Gross=("Gross_USD", "mean"),
            Film_Count=("Gross_USD", "count"),
        )
        .reset_index()
        .sort_values("Decade")
    )
    decade_data["Avg_Gross_M"] = decade_data["Avg_Gross"] / 1_000_000

    fig_line = px.line(
        decade_data,
        x="Decade",
        y="Avg_Gross_M",
        title="Average Box Office Gross by Decade",
        labels={"Decade": "Decade", "Avg_Gross_M": "Avg Gross (USD Millions)"},
        markers=True,
        text="Avg_Gross_M",
    )
    fig_line.update_traces(
        line_color="#1A4A7A",
        marker=dict(color="#B8860B", size=9, line=dict(color="#FFFFFF", width=2)),
        texttemplate="$%{text:.0f}M",
        textposition="top center",
        textfont=dict(color="#1A1A2E", size=10),
    )
    fig_line.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font_color="#1A1A2E",
        title_font_color="#1A1A2E",
        xaxis=dict(gridcolor="#E0E0E0", linecolor="#CCCCCC", tickfont=dict(color="#1A1A2E")),
        yaxis=dict(gridcolor="#E0E0E0", tickfont=dict(color="#1A1A2E")),
        margin=dict(t=50, b=40),
    )
    st.plotly_chart(fig_line, use_container_width=True)


# CHART 3: Heatmap — Film Count by Genre and Decade (moved above scatter)
st.markdown("#### Film Volume by Genre and Decade")

pivot_df = (
    df_filtered.groupby(["Primary_Genre", "Decade"])
    .size()
    .reset_index(name="Count")
    .pivot(index="Primary_Genre", columns="Decade", values="Count")
    .fillna(0)
)

fig_heat = go.Figure(
    data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns.tolist(),
        y=pivot_df.index.tolist(),
        colorscale=[
            [0.0, "#EAF2FB"],
            [0.3, "#A8C8E8"],
            [0.6, "#2E6DA4"],
            [1.0, "#1A3A6A"],
        ],
        showscale=True,
        hoverongaps=False,
        hovertemplate="Genre: %{y}<br>Decade: %{x}<br>Films: %{z}<extra></extra>",
        text=pivot_df.values.astype(int),
        texttemplate="%{text}",
        textfont=dict(color="#1A1A2E", size=11),
    )
)
fig_heat.update_layout(
    title="Number of Top-Rated Films by Genre and Decade",
    title_font_color="#1A1A2E",
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font_color="#1A1A2E",
    xaxis=dict(title="Decade", gridcolor="#E0E0E0", tickfont=dict(color="#1A1A2E")),
    yaxis=dict(title="Primary Genre", tickfont=dict(color="#1A1A2E")),
    margin=dict(t=60, b=40),
    height=420,
)
st.plotly_chart(fig_heat, use_container_width=True)


# CHART 4: Scatter Plot — IMDB Rating vs. Metacritic Score
st.markdown("#### Critical Consensus vs. Audience Reception: IMDB Rating vs. Metacritic Score")

scatter_df = df_filtered.dropna(subset=["Meta_score", "Gross_USD"]).copy()
scatter_df["Gross_M"] = scatter_df["Gross_USD"] / 1_000_000

fig_scatter = px.scatter(
    scatter_df,
    x="Meta_score",
    y="IMDB_Rating",
    size="Gross_M",
    color="Primary_Genre",
    hover_name="Series_Title",
    hover_data={"Year": True, "Gross_M": ":.1f", "Primary_Genre": True},
    title="IMDB Rating vs. Metacritic Score (Bubble Size = Box Office Gross)",
    labels={
        "Meta_score": "Metacritic Score (Critics)",
        "IMDB_Rating": "IMDB Rating (Audience)",
        "Gross_M": "Gross (USD M)",
        "Primary_Genre": "Genre",
    },
    color_discrete_sequence=CHART_COLORS,
    opacity=0.8,
)
fig_scatter.update_layout(
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font_color="#1A1A2E",
    title_font_color="#1A1A2E",
    xaxis=dict(gridcolor="#E0E0E0", linecolor="#CCCCCC", tickfont=dict(color="#1A1A2E")),
    yaxis=dict(gridcolor="#E0E0E0", tickfont=dict(color="#1A1A2E")),
    legend=dict(bgcolor="#F7F9FC", bordercolor="#D0D8E4", font=dict(color="#1A1A2E")),
    margin=dict(t=60, b=40),
)
st.plotly_chart(fig_scatter, use_container_width=True)


# ─────────────────────────────────────────────
# KEY FINDINGS
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">Key Findings</div>', unsafe_allow_html=True)

st.markdown("""
<div class="insight-box">
    <strong>Finding 1 — Crime tops audience ratings, but barely.</strong>
    Crime leads with an 8.02 IMDB average, yet every major genre falls within a 0.12-point band (7.90–8.02).
    High audience ratings are broadly distributed, not genre-specific.
</div>

<div class="insight-box">
    <strong>Finding 2 — Action earns 4× Drama's box office despite near-equal ratings.</strong>
    Action ($142M avg) and Drama ($38.7M avg) sit just 0.01 points apart on IMDB, yet the revenue gap is enormous.
    Animation ($128M) similarly towers over critically admired genres like Crime and Mystery commercially.
</div>

<div class="insight-box">
    <strong>Finding 3 — Box office power shifted decisively from Drama → Action, and never reversed.</strong>
    Drama led through the 1940s, Horror briefly spiked in the 1970s (Jaws, Halloween), then Action took over
    in the 1980s and has grown 94% since from $104M/film to $202M in the 2010s. Animation's rise in the
    1990s–2000s is the only serious challenge to Action's commercial dominance.
</div>

<div class="insight-box">
    <strong>Finding 4 — Ratings prestige migrated from Westerns/Crime to Animation and back.</strong>
    Westerns commanded the highest average ratings in the 1960s, Crime dominated most other decades, but
    Animation briefly seized the top-rated position in the 2000s (7.95 avg) with the Pixar golden era effect
    before Crime reclaimed it in the 2010s.
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# OPTIONAL: FILTERED DATA TABLE + DOWNLOAD
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">Filtered Dataset</div>', unsafe_allow_html=True)

display_cols = [
    "Series_Title", "Year", "Primary_Genre", "IMDB_Rating",
    "Meta_score", "Runtime_Min", "Director", "Gross_USD",
]
df_display = df_filtered[display_cols].copy()
df_display["Gross_USD"] = df_display["Gross_USD"].apply(
    lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
)
df_display.columns = [
    "Title", "Year", "Genre", "IMDB Rating",
    "Metacritic", "Runtime (min)", "Director", "Box Office Gross",
]

st.dataframe(df_display, use_container_width=True, height=300)

# Download button for filtered CSV export
csv_export = df_filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Filtered Data as CSV",
    data=csv_export,
    file_name="imdb_filtered_export.csv",
    mime="text/csv",
)
