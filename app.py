"""
IMDB Top 1000 Movies Dashboard
BAN-461 Capstone Assignment
Analytical Question: Which movie genres earn the highest ratings and box office revenue,
and has that changed over the decades?

Created with the help of Claude AI. Comments also generated with the help of Claude AI, but reviewed by Mikayla.

"""

# Standard library imports for data manipulation, visualization, and the web app framework
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ─────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────
# Sets the browser tab title, icon, and default layout for the Streamlit app.
# layout="wide" uses the full browser width; "expanded" keeps the sidebar open by default.

st.set_page_config(
    page_title="IMDB Top 1000 Analytics",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS STYLING — White background, dark readable text
# ─────────────────────────────────────────────
# Injects custom CSS into the Streamlit app to override default styling.
# Uses a professional palette: white background, navy text,
# and dark gold accents. unsafe_allow_html=True is required to render raw HTML/CSS.

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
# @st.cache_data tells Streamlit to cache the result of this function so it only
# runs once per session, preventing slow CSV re-reads on every user interaction.

@st.cache_data
def load_data():
    df = pd.read_csv("imdb_top_1000.csv")

    # Clean Runtime: extract numeric minutes
    # The raw "Runtime" column contains strings like "142 min"; regex extracts just the number.
    df["Runtime_Min"] = df["Runtime"].str.extract(r"(\d+)").astype(float)

    # Clean Gross: remove commas, convert to numeric
    # Raw values are formatted strings like "28,341,469"; strip commas then cast to float.
    # errors="coerce" turns any unparseable values into NaN instead of raising an error.
    df["Gross_USD"] = pd.to_numeric(
        df["Gross"].str.replace(",", "", regex=False), errors="coerce"
    )

    # Clean Released_Year: remove non-numeric rows (e.g., 'PG')
    # Some rows have non-year data in the Released_Year column; coercing to numeric
    # converts those to NaN, which are then dropped to keep only valid year rows.
    df["Year"] = pd.to_numeric(df["Released_Year"], errors="coerce")
    df = df.dropna(subset=["Year"])
    df["Year"] = df["Year"].astype(int)

    # Create decade column for grouping
    # Integer division by 10, then multiply back, yields the decade start year (e.g., 1987 → 1980).
    # Adding "s" produces a readable label like "1980s".
    df["Decade"] = (df["Year"] // 10 * 10).astype(str) + "s"

    # Extract primary genre (first listed)
    # The Genre column contains comma-separated values like "Action, Adventure, Sci-Fi".
    # Splitting on "," and taking the first element gives the film's main genre.
    df["Primary_Genre"] = df["Genre"].str.split(",").str[0].str.strip()

    return df


# Load the cleaned dataset into a module-level variable for use throughout the app.
df_raw = load_data()


# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────

st.sidebar.markdown("## Filters")
st.sidebar.markdown("---")

# Filter 1: Decade range slider
# Dynamically compute min/max years from the data so the slider always matches the dataset.
min_year = int(df_raw["Year"].min())
max_year = int(df_raw["Year"].max())

# Slider returns a tuple (start_year, end_year) that is used to filter the dataframe below.
# Default view starts from 1970 to focus on the modern era of cinema.
year_range = st.sidebar.slider(
    "Release Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(1970, max_year),
    step=1,
)

# Filter 2: Primary genre multiselect
# Builds the list of genre options from unique values in the cleaned data.
# All major genres are pre-selected by default so the dashboard is immediately populated.
all_genres = sorted(df_raw["Primary_Genre"].dropna().unique())
selected_genres = st.sidebar.multiselect(
    "Primary Genre",
    options=all_genres,
    default=["Action", "Adventure", "Animation", "Biography", "Comedy", "Crime", "Drama", "Family", "Fantasy", "Film-Noir", "Horror", "Mystery", "Thriller", "Western"],
)

# Filter 3: Minimum IMDB rating slider
# Allows users to raise the quality floor; the dataset only contains ratings from 7.6 to 9.3.
# format="%.1f" displays one decimal place on the slider handle.
min_rating = st.sidebar.slider(
    "Minimum IMDB Rating",
    min_value=7.6,
    max_value=9.3,
    value=7.6,
    step=0.1,
    format="%.1f",
)

# Footer credit line at the bottom of the sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<span style='color:#4A4A6A; font-size:0.8rem;'>IMDB Top 1000 Dataset · BAN-461 Capstone</span>",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────

# Build the working dataframe by applying all three sidebar filters simultaneously.
# The genre condition short-circuits to True (no genre filtering) if the multiselect is empty,
# preventing an accidentally blank dashboard when a user clears all genre selections.
# .copy() avoids SettingWithCopyWarning when modifying df_filtered downstream.
df_filtered = df_raw[
    (df_raw["Year"] >= year_range[0])
    & (df_raw["Year"] <= year_range[1])
    & (df_raw["Primary_Genre"].isin(selected_genres) if selected_genres else True)
    & (df_raw["IMDB_Rating"] >= min_rating)
].copy()


# ─────────────────────────────────────────────
# DASHBOARD HEADER
# ─────────────────────────────────────────────

# Renders the main title, subtitle, and the framing analytical question using
# custom CSS classes defined in the style block above.
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
# Each metric shows the filtered value alongside a delta (difference) vs. the full dataset,
# giving immediate context for how the current filter selection compares to the overall average.
avg_rating_filtered = df_filtered["IMDB_Rating"].mean()
avg_rating_all = df_raw["IMDB_Rating"].mean()
rating_delta = avg_rating_filtered - avg_rating_all

# Gross values are divided by 1,000,000 to display in millions (easier to read on the card).
avg_gross_filtered = df_filtered["Gross_USD"].dropna().mean() / 1_000_000
avg_gross_all = df_raw["Gross_USD"].dropna().mean() / 1_000_000
gross_delta = avg_gross_filtered - avg_gross_all

# Identify the most frequently occurring genre in the filtered set for the "top genre" card.
# Guards against an empty dataframe (e.g., if filters exclude all films) with a fallback to "N/A".
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
# Express the top genre's count as a percentage of the total filtered films.
top_genre_pct = (top_genre_count / total_films * 100) if total_films > 0 else 0

avg_metascore_filtered = df_filtered["Meta_score"].dropna().mean()
avg_metascore_all = df_raw["Meta_score"].dropna().mean()
meta_delta = avg_metascore_filtered - avg_metascore_all

# Lay out the four KPI cards side-by-side in equal-width columns.
col1, col2, col3, col4 = st.columns(4)

# KPI 1: Count of films matching the current filters vs. the full 1000-film dataset.
col1.metric(
    label="Films in Selection",
    value=f"{total_films:,}",
    delta=f"{total_films - len(df_raw):+,} vs. full dataset",
)

# KPI 2: Average IMDB audience rating for filtered films, delta vs. full dataset average.
col2.metric(
    label="Avg IMDB Rating",
    value=f"{avg_rating_filtered:.2f}" if not df_filtered.empty else "N/A",
    delta=f"{rating_delta:+.2f} vs. all films",
)

# KPI 3: Average box office gross in millions for filtered films, delta vs. full dataset.
col3.metric(
    label="Avg Box Office Gross",
    value=f"${avg_gross_filtered:.1f}M" if not df_filtered.empty else "N/A",
    delta=f"${gross_delta:+.1f}M vs. all films",
)

# KPI 4: Average Metacritic critic score for filtered films, delta vs. full dataset.
col4.metric(
    label="Avg Metacritic Score",
    value=f"{avg_metascore_filtered:.0f}" if not df_filtered.empty else "N/A",
    delta=f"{meta_delta:+.1f} vs. all films",
)


# ─────────────────────────────────────────────
# CHART 1: Avg IMDB Rating by Primary Genre (Bar Chart)
# ─────────────────────────────────────────────

st.markdown('<div class="section-header">Visualizations</div>', unsafe_allow_html=True)

# Consistent color palette shared across all charts to maintain visual cohesion.
# Ten distinct, accessible colors designed to stand out on a white background.
CHART_COLORS = [
    "#1A4A7A", "#B8860B", "#7B2D8B", "#C0392B", "#1A6B3C",
    "#0E6B8C", "#D4520A", "#2C3E50", "#6B4226", "#4A235A"
]

# Split the visualization section into two equal columns for side-by-side charts.
col_left, col_right = st.columns(2)

with col_left:
    # CHART 1: Dual-axis grouped bar — Avg IMDB Rating AND Avg Gross by Genre
    # Aggregates the filtered data by genre, computing mean rating and mean gross.
    # dropna(subset=["Avg_Gross"]) removes genres with no box office data.
    # Sorted by Avg_Rating descending; limited to top 12 genres to keep the chart readable.
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
    # Convert raw dollar gross to millions for a cleaner axis label.
    genre_summary["Avg_Gross_M"] = genre_summary["Avg_Gross"] / 1_000_000

    # Use a go.Figure (low-level Plotly) instead of px so two independent y-axes can be defined.
    fig_dual = go.Figure()

    # Bar 1: Avg IMDB Rating — left y-axis
    # Plotly uses yaxis="y1" (left) and yaxis="y2" (right) to bind traces to different axes.
    # offsetgroup=1 ensures this bar is grouped separately from the gross bar.
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
    # Plotted on a separate y-axis (y2) so the two very different scales don't compress each other.
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
        # Left y-axis: IMDB Rating scale (7.0–9.8 keeps bars proportional without a misleading zero baseline).
        yaxis=dict(
            title="Avg IMDB Rating",
            range=[7.0, 9.8],
            gridcolor="#E0E0E0",
            tickfont=dict(color="#1A4A7A"),
            title_font=dict(color="#1A4A7A"),
        ),
        # Right y-axis: Box office gross scale; overlaying="y" anchors it to the same plot area.
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
    # CHART 2: Average Gross by Decade per Genre (Multi-line Chart)
    # Groups by both Decade and Primary_Genre to produce one data point per genre per decade.
    # The sort_values key extracts the numeric year from the "1980s"-style label so decades
    # sort chronologically rather than alphabetically.
    decade_genre_data = (
        df_filtered.dropna(subset=["Gross_USD"])
        .groupby(["Decade", "Primary_Genre"])
        .agg(Avg_Gross=("Gross_USD", "mean"))
        .reset_index()
        .sort_values("Decade", key=lambda x: x.str.extract(r"(\d+)")[0].astype(int))
    )
    decade_genre_data["Avg_Gross_M"] = decade_genre_data["Avg_Gross"] / 1_000_000

    # Build an explicitly sorted list of decades to pass to category_orders,
    # ensuring Plotly's x-axis is in true chronological order regardless of data row order.
    sorted_decades = sorted(
        decade_genre_data["Decade"].unique(),
        key=lambda d: int(d.replace("s", ""))
    )

    # px.line draws one colored line per genre; markers=True adds data-point dots on each line.
    fig_line = px.line(
        decade_genre_data,
        x="Decade",
        y="Avg_Gross_M",
        color="Primary_Genre",
        title="Average Box Office Gross by Decade",
        labels={"Decade": "Decade", "Avg_Gross_M": "Avg Gross (USD Millions)", "Primary_Genre": "Genre"},
        markers=True,
        color_discrete_sequence=CHART_COLORS,
        category_orders={"Decade": sorted_decades},
    )
    fig_line.update_traces(
        marker=dict(size=7, line=dict(color="#FFFFFF", width=1.5)),
    )
    fig_line.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font_color="#1A1A2E",
        title_font_color="#1A1A2E",
        xaxis=dict(gridcolor="#E0E0E0", linecolor="#CCCCCC", tickfont=dict(color="#1A1A2E")),
        yaxis=dict(gridcolor="#E0E0E0", tickfont=dict(color="#1A1A2E")),
        legend=dict(
            bgcolor="#F7F9FC",
            bordercolor="#D0D8E4",
            font=dict(color="#1A1A2E"),
            title=dict(text="Genre"),
        ),
        margin=dict(t=50, b=40),
    )
    st.plotly_chart(fig_line, use_container_width=True)


# CHART 3: Heatmap — Avg IMDB Rating by Genre and Decade
st.markdown("#### Average IMDB Rating by Genre and Decade")

# Build a pivot table: rows = genres, columns = decades, cell values = mean IMDB rating.
# This 2-D structure is exactly what go.Heatmap expects for its z (color intensity) values.
pivot_df = (
    df_filtered.groupby(["Primary_Genre", "Decade"])["IMDB_Rating"]
    .mean()
    .reset_index(name="Avg_Rating")
    .pivot(index="Primary_Genre", columns="Decade", values="Avg_Rating")
)

# go.Heatmap renders the pivot as a color-coded grid.
# z=pivot_df.values provides the 2-D array of rating values that drive cell colors.
# The custom colorscale goes from light blue (low ratings) to deep navy (high ratings).
# hoverongaps=False suppresses tooltips on NaN cells (genre/decade combos with no data).
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
        hovertemplate="Genre: %{y}<br>Decade: %{x}<br>Avg IMDB Rating: %{z:.2f}<extra></extra>",
        # Display the numeric rating directly inside each cell for quick reading.
        text=pivot_df.values,
        texttemplate="%{text:.2f}",
        textfont=dict(color="#1A1A2E", size=11),
    )
)
fig_heat.update_layout(
    title="Average IMDB Rating by Genre and Decade",
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

# Drop rows missing either Metacritic score or gross so every bubble has a valid size and position.
scatter_df = df_filtered.dropna(subset=["Meta_score", "Gross_USD"]).copy()
scatter_df["Gross_M"] = scatter_df["Gross_USD"] / 1_000_000

# Bubble chart: x = critic score, y = audience score, bubble size = box office gross.
# This lets users spot films that critics and audiences agreed (or disagreed) on,
# and whether big-budget films cluster differently than smaller ones.
# hover_name shows the film title in the tooltip; hover_data adds year, gross, and genre.
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

# Static narrative section summarizing the four main analytical conclusions drawn from the data.
# Rendered as styled HTML "insight-box" cards defined in the CSS block at the top of the file.
st.markdown('<div class="section-header">Key Findings</div>', unsafe_allow_html=True)

st.markdown("""
<div class="insight-box">
    <strong>Finding 1 — Crime tops audience ratings, but barely.</strong>
    Crime leads with an 8.02 IMDB average, yet every major genre falls within a 0.12-point band (7.90–8.02).
    High audience ratings are broadly distributed, not genre-specific. This finding excluded the Western genre that did not meet a minimum threshold of 5+ films to help ensure findings remain statistically significant.
</div>

<div class="insight-box">
    <strong>Finding 2 — Action earns 4× Drama's box office despite near-equal ratings.</strong>
    Action ($142M avg) and Drama ($38.7M avg) sit just 0.01 points apart on IMDB, yet the revenue gap is enormous.
    Animation ($128M) similarly towers over critically admired genres like Crime and Mystery commercially. This finding similarly excluded the Family genre that did not meet the minimum 5+ films threshold.
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

# Select only the columns relevant for end-user display; drop internal/intermediate columns.
display_cols = [
    "Series_Title", "Year", "Primary_Genre", "IMDB_Rating",
    "Meta_score", "Runtime_Min", "Director", "Gross_USD",
]
df_display = df_filtered[display_cols].copy()

# Format the gross column as a dollar string (e.g., "$28,341,469") for readability.
# Rows with missing gross data display "N/A" instead of a blank or NaN.
df_display["Gross_USD"] = df_display["Gross_USD"].apply(
    lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
)

# Rename columns to friendly display labels before rendering the table.
df_display.columns = [
    "Title", "Year", "Genre", "IMDB Rating",
    "Metacritic", "Runtime (min)", "Director", "Box Office Gross",
]

# Render the table with a fixed height to keep the page layout compact.
# use_container_width=True stretches the table to fill its column.
st.dataframe(df_display, use_container_width=True, height=300)

# Download button for filtered CSV export
# Encodes the full filtered dataframe (not just display columns) as a UTF-8 CSV byte string
# and offers it to the user as a downloadable file named "imdb_filtered_export.csv".
csv_export = df_filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Filtered Data as CSV",
    data=csv_export,
    file_name="imdb_filtered_export.csv",
    mime="text/csv",
)
