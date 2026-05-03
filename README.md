# IMDB Top 1000 Cinema Analytics Dashboard

**BAN-461: Advanced Data Modeling Systems — Capstone Project**

## Analytical Question

What factors — genre, era, runtime, and critical reception — most strongly predict a film's IMDB audience rating and box office gross, and how have these relationships shifted across decades of cinema?

## Dashboard Features

### KPI Metrics
- Total films in current selection (with delta vs. full dataset)
- Average IMDB Rating (with delta vs. all films)
- Average Box Office Gross in USD millions
- Average Metacritic Score

### Interactive Filters (Sidebar)
- Release Year Range — slider to restrict the decade window
- Primary Genre — multiselect to focus on specific genres
- Minimum IMDB Rating — slider to set a quality floor

### Visualizations
1. **Bar Chart** — Average IMDB Rating by Primary Genre
2. **Line Chart** — Average Box Office Gross by Decade
3. **Scatter/Bubble Plot** — IMDB Rating vs. Metacritic Score (sized by gross, colored by genre)
4. **Heatmap** — Film volume by Genre and Decade

### Additional Features
- Key Findings section with four analytical conclusions
- Filtered data table (`st.dataframe`)
- CSV export via `st.download_button`
- `@st.cache_data` for data loading performance

## Dataset

`imdb_top_1000.csv` — IMDB's top 1000 rated films as scraped from the IMDB website.
Columns include: title, year, genre, IMDB rating, Metacritic score, runtime, director, cast, votes, and box office gross.

## Setup & Deployment

### Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Community Cloud Deployment
1. Push this repository to a public GitHub repo
2. Visit https://share.streamlit.io
3. Connect your GitHub account and select this repo
4. Set the main file path to `app.py`
5. Click Deploy

## Repository Structure

```
├── app.py                  # Main Streamlit application
├── imdb_top_1000.csv       # Dataset
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Technology Stack

Python · Streamlit · Plotly Express · pandas · NumPy
