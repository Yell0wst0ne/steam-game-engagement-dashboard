from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Steam Signals | Game Engagement",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).parent / "data" / "steam_games.csv"
COLORS = {
    "ink": "#f4f2ff",
    "muted": "#a9a8bd",
    "grid": "rgba(196, 191, 224, .12)",
    "purple": "#a78bfa",
    "cyan": "#53d8d2",
    "pink": "#f08ab5",
    "surface": "#171626",
}

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    .stApp { background: radial-gradient(ellipse at 82% 0%, #252043 0%, #11111d 38%, #101019 100%); }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.035em; }
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1440px; }
    .hero-kicker { color: #a78bfa; text-transform: uppercase; font-size: .75rem; letter-spacing: .18em; font-weight: 700; }
    .hero-copy { color: #b9b7ca; font-size: 1.04rem; max-width: 850px; margin-top: -.35rem; }
    .insight-box { border: 1px solid rgba(167,139,250,.24); background: linear-gradient(135deg, rgba(167,139,250,.12), rgba(83,216,210,.055)); padding: 1rem 1.15rem; border-radius: 14px; color: #eae8f5; min-height: 92px; }
    .insight-label { color: #a9a8bd; font-size: .72rem; letter-spacing: .11em; text-transform: uppercase; margin-bottom: .35rem; }
    div[data-testid="stMetric"] { background: rgba(23,22,38,.8); border: 1px solid rgba(196,191,224,.12); padding: 1rem 1.1rem; border-radius: 14px; }
    div[data-testid="stMetricLabel"] { color: #a9a8bd; }
    div[data-testid="stMetricValue"] { color: #f4f2ff; font-family: 'Space Grotesk', sans-serif; }
    div[data-testid="stPlotlyChart"] { background: rgba(23,22,38,.72); border: 1px solid rgba(196,191,224,.1); border-radius: 14px; padding: .25rem; }
    section[data-testid="stSidebar"] { background: #12111e; border-right: 1px solid rgba(196,191,224,.1); }
    .source-note { color: #a9a8bd; font-size: .82rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH)
    for column in ["release_year", "price_usd", "peak_ccu", "positive_reviews", "negative_reviews", "total_reviews", "positive_share", "recommendations"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["primary_genre"] = data["primary_genre"].fillna("Unclassified")
    return data


df = load_data()
min_year, max_year = int(df.release_year.min()), int(df.release_year.max())
genres = sorted(value for value in df.primary_genre.dropna().unique() if value != "Unclassified")

with st.sidebar:
    st.markdown("## 🎛️ Explore the catalog")
    years = st.slider("Release years", min_year, max_year, (max(2000, min_year), max_year))
    selected_genres = st.multiselect("Primary genre", genres, default=[])
    price_filter = st.radio("Price", ["All games", "Free to play", "Paid games"], horizontal=False)
    minimum_reviews = st.slider("Minimum reviews for sentiment charts", 0, 1000, 50, step=25)
    st.markdown("---")
    st.caption("Review sentiment uses the selected minimum review count. A game’s first listed Steam genre is used for genre comparisons.")

filtered = df[df.release_year.between(years[0], years[1])].copy()
if selected_genres:
    filtered = filtered[filtered.primary_genre.isin(selected_genres)]
if price_filter == "Free to play":
    filtered = filtered[filtered.price_usd.eq(0)]
elif price_filter == "Paid games":
    filtered = filtered[filtered.price_usd.gt(0)]

if filtered.empty:
    st.title("No games match these filters")
    st.info("Try a wider year range or select fewer genres.")
    st.stop()

st.markdown('<div class="hero-kicker">Steam catalog · engagement signals</div>', unsafe_allow_html=True)
st.title("What makes a Steam game break through?")
st.markdown(
    '<p class="hero-copy">Explore how player activity, reviews, genre, release timing, and price fit together across a snapshot of the Steam catalog. Popularity here means engagement signals, not copies sold.</p>',
    unsafe_allow_html=True,
)

sentiment = filtered[filtered.total_reviews.ge(minimum_reviews) & filtered.total_reviews.gt(0)].copy()
positive_total = sentiment.positive_reviews.sum()
all_reviews = sentiment.total_reviews.sum()
overall_positive = positive_total / all_reviews if all_reviews else float("nan")
active_games = filtered[filtered.peak_ccu.gt(0)]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Games in view", f"{len(filtered):,}")
m2.metric("Games with recorded peak players", f"{filtered.peak_ccu.gt(0).sum():,}")
m3.metric("Positive share of reviews", f"{overall_positive:.0%}" if pd.notna(overall_positive) else "—", help=f"Weighted across games with at least {minimum_reviews:,} reviews.")
m4.metric("Median peak concurrent players", f"{active_games.peak_ccu.median():,.0f}" if not active_games.empty else "—", help="Median among games with a recorded peak above zero.")

genre_activity = (
    active_games.groupby("primary_genre", as_index=False)
    .agg(median_peak_ccu=("peak_ccu", "median"), games=("game", "size"))
    .query("games >= 100")
    .nlargest(12, "median_peak_ccu")
    .sort_values("median_peak_ccu")
)
yearly = filtered.groupby("release_year", as_index=False).agg(games=("game", "size"))
genre_reviews = (
    sentiment.groupby("primary_genre", as_index=False)
    .agg(positive=("positive_reviews", "sum"), total=("total_reviews", "sum"), games=("game", "size"))
)
genre_reviews["positive_share"] = genre_reviews.positive / genre_reviews.total
genre_reviews = genre_reviews.query("games >= 100").nlargest(12, "positive_share").sort_values("positive_share")

left, right = st.columns(2, gap="large")
with left:
    st.subheader("The player base is not evenly spread")
    st.caption("Median recorded peak concurrent players by primary genre; only games with a nonzero peak are included.")
    if genre_activity.empty:
        st.info("Not enough genres with 100+ active games in this selection.")
    else:
        fig = px.bar(genre_activity, x="median_peak_ccu", y="primary_genre", orientation="h", text="median_peak_ccu", custom_data=["games"], color="median_peak_ccu", color_continuous_scale=["#5b4f88", COLORS["cyan"]])
        fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", hovertemplate="%{y}<br>Median peak: %{x:,.0f}<br>Games with activity: %{customdata[0]:,}<extra></extra>")
        fig.update_layout(coloraxis_showscale=False, xaxis_title="Median peak concurrent players", yaxis_title="", height=420)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with right:
    st.subheader("Release volume changed over time")
    st.caption("Number of games released per year in this filtered slice of Steam.")
    fig = px.area(yearly, x="release_year", y="games", markers=True)
    fig.update_traces(line_color=COLORS["purple"], fillcolor="rgba(167,139,250,.18)", marker_color=COLORS["cyan"], hovertemplate="%{x}: %{y:,} games<extra></extra>")
    fig.update_layout(xaxis_title="Release year", yaxis_title="Games", height=420)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Price and review sentiment")
    st.caption(f"Each dot is a game with at least {minimum_reviews:,} reviews. Review counts are capped visually at the 99th percentile.")
    if sentiment.empty:
        st.info("No games meet the review threshold. Lower the minimum reviews slider.")
    else:
        scatter = sentiment.copy()
        cap = max(1, scatter.total_reviews.quantile(.99))
        scatter["review_size"] = scatter.total_reviews.clip(upper=cap)
        scatter["price_label"] = scatter.price_usd.map(lambda value: "Free" if value == 0 else "Paid")
        # A fixed, stable sample keeps the interactive chart quick for large selections.
        if len(scatter) > 8000:
            scatter = scatter.sample(8000, random_state=21)
        fig = px.scatter(scatter, x="price_usd", y="positive_share", size="review_size", color="price_label", color_discrete_map={"Free": COLORS["cyan"], "Paid": COLORS["pink"]}, hover_name="game", hover_data={"primary_genre": True, "release_year": True, "total_reviews": ":,", "price_usd": ":$.2f", "positive_share": ":.0%", "review_size": False, "price_label": False})
        fig.update_traces(marker={"opacity": .55, "line": {"width": 0}})
        fig.update_layout(xaxis_title="Current listed price (USD)", yaxis_title="Positive review share", yaxis_tickformat=".0%", height=420, legend_title="Price type")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with right:
    st.subheader("Genres with the strongest review signal")
    st.caption(f"Review-weighted positive share, limited to genres with 100+ games meeting the {minimum_reviews:,}-review threshold.")
    if genre_reviews.empty:
        st.info("Not enough review volume in this selection to compare genres.")
    else:
        fig = px.bar(genre_reviews, x="positive_share", y="primary_genre", orientation="h", text="positive_share", custom_data=["games", "total"], color="positive_share", color_continuous_scale=["#5b4f88", COLORS["purple"]])
        fig.update_traces(texttemplate="%{x:.0%}", textposition="outside", hovertemplate="%{y}<br>Positive share: %{x:.1%}<br>Games: %{customdata[0]:,}<br>Reviews: %{customdata[1]:,}<extra></extra>")
        fig.update_layout(coloraxis_showscale=False, xaxis_title="Positive share of reviews", xaxis_tickformat=".0%", yaxis_title="", height=420)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.subheader("A few patterns in this selection")
insight_cols = st.columns(3, gap="medium")
if not genre_activity.empty:
    leader = genre_activity.iloc[-1]
    insight_cols[0].markdown(f'<div class="insight-box"><div class="insight-label">Peak activity</div><b>{leader.primary_genre}</b> leads on median peak concurrent players at <b>{leader.median_peak_ccu:,.0f}</b> among genres with at least 100 active games.</div>', unsafe_allow_html=True)
else:
    insight_cols[0].info("Choose a wider selection to compare activity by genre.")
if not genre_reviews.empty:
    review_leader = genre_reviews.iloc[-1]
    insight_cols[1].markdown(f'<div class="insight-box"><div class="insight-label">Review signal</div><b>{review_leader.primary_genre}</b> has the highest review-weighted positive share at <b>{review_leader.positive_share:.1%}</b> in this selection.</div>', unsafe_allow_html=True)
else:
    insight_cols[1].info("Choose a wider selection to compare review signals.")
if not yearly.empty:
    peak_year = yearly.loc[yearly.games.idxmax()]
    insight_cols[2].markdown(f'<div class="insight-box"><div class="insight-label">Release volume</div><b>{int(peak_year.release_year)}</b> is the busiest release year in this selection, with <b>{int(peak_year.games):,}</b> games.</div>', unsafe_allow_html=True)

st.subheader("Games with the largest recorded peak audiences")
top_games = filtered.nlargest(12, "peak_ccu")[["game", "release_year", "primary_genre", "peak_ccu", "price_usd", "positive_reviews", "negative_reviews"]].copy()
top_games["positive_review_share"] = top_games.positive_reviews.div((top_games.positive_reviews + top_games.negative_reviews).replace(0, pd.NA))
top_games = top_games.drop(columns=["positive_reviews", "negative_reviews"]).rename(columns={"game": "Game", "release_year": "Year", "primary_genre": "Primary genre", "peak_ccu": "Peak concurrent players", "price_usd": "Price (USD)", "positive_review_share": "Positive review share"})
st.dataframe(top_games, hide_index=True, use_container_width=True, column_config={"Peak concurrent players": st.column_config.NumberColumn(format="%d"), "Price (USD)": st.column_config.NumberColumn(format="$%.2f"), "Positive review share": st.column_config.NumberColumn(format="percent")})

with st.expander("About the data and how to read this dashboard"):
    st.markdown(
        """
        - **Source:** [Fronkon Games Steam Games Dataset](https://huggingface.co/datasets/FronkonGames/steam-games-dataset), a public dataset built from Steam's API and Steam Spy. This project uses a snapshot of 124,146 rows retrieved on October 14, 2026.
        - **Engagement is not sales:** peak concurrent players and review counts are signals of player activity. They do not reveal copies sold, revenue, or lifetime popularity across all platforms.
        - **Review sentiment:** positive share is positive reviews divided by all positive and negative reviews. The sidebar threshold filters out titles with very few reviews.
        - **Genres:** a title can have multiple Steam genres; for clean comparisons this dashboard assigns it to the first listed genre.
        - **Prices:** listed USD prices are a snapshot and can change with discounts or regional pricing.
        """
    )
st.markdown('<p class="source-note">Built for exploration, not prediction. Correlation between price, reviews, and concurrent players does not show that one causes another.</p>', unsafe_allow_html=True)
