"""Movie recommendation engine using TF-IDF cosine similarity."""

import os
import pickle
import requests
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import linear_kernel
from dotenv import load_dotenv

load_dotenv()

# Paths to data files (relative to project root)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DF_PATH = os.path.join(BASE_DIR, "df.pkl")
INDICES_PATH = os.path.join(BASE_DIR, "indices.pkl")
TFIDF_PATH = os.path.join(BASE_DIR, "tfIDF.pkl")

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w500"

# Global state
df = None
indices = None
tfidf_vectorizer = None
tfidf_matrix = None


def load_model():
    """Load all pickle files and precompute the TF-IDF matrix."""
    global df, indices, tfidf_vectorizer, tfidf_matrix

    print("⏳ Loading movie data...")
    with open(DF_PATH, "rb") as f:
        df = pickle.load(f)

    with open(INDICES_PATH, "rb") as f:
        indices = pickle.load(f)

    with open(TFIDF_PATH, "rb") as f:
        tfidf_vectorizer = pickle.load(f)

    # Build TF-IDF matrix from the 'Tags' column (or 'tags' as fallback)
    tag_col = "Tags" if "Tags" in df.columns else "tags"
    df[tag_col] = df[tag_col].fillna("")
    tfidf_matrix = tfidf_vectorizer.transform(df[tag_col])

    # Clean up NaN values for JSON serialization
    df["overview"] = df["overview"].fillna("")
    df["genres"] = df["genres"].fillna("")
    df["tagline"] = df["tagline"].fillna("")
    df["vote_average"] = pd.to_numeric(df["vote_average"], errors="coerce").fillna(0.0)
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce").fillna(0.0)
    df["title"] = df["title"].fillna("")

    print(f"✅ Loaded {len(df)} movies, TF-IDF matrix shape: {tfidf_matrix.shape}")


# Poster URL cache  {title: poster_url}
_poster_cache = {}


def _fetch_poster_path(title: str) -> str:
    """Fetch poster path from TMDB (cached)."""
    if title in _poster_cache:
        return _poster_cache[title]
    if not TMDB_API_KEY:
        return ""
    try:
        resp = requests.get(
            TMDB_SEARCH_URL,
            params={"api_key": TMDB_API_KEY, "query": title},
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results and results[0].get("poster_path"):
                url = TMDB_IMG_BASE + results[0]["poster_path"]
                _poster_cache[title] = url
                return url
    except Exception:
        pass
    _poster_cache[title] = ""
    return ""


def _build_movie(row) -> dict:
    """Build a movie dict from a DataFrame row."""
    title = str(row.get("title", ""))
    return {
        "title": title,
        "overview": str(row.get("overview", ""))[:200],
        "genres": str(row.get("genres", "")),
        "tagline": str(row.get("tagline", "")),
        "vote_average": float(row.get("vote_average", 0)),
        "popularity": float(row.get("popularity", 0)),
        "poster_url": None,
    }


def get_recommendations(title: str, n: int = 12):
    """Get top-n movie recommendations for a given title using cosine similarity."""
    # Try exact match first
    title_lower = title.lower().strip()
    matches = indices[indices.index.str.lower() == title_lower]

    if matches.empty:
        # Try partial match
        matches = indices[indices.index.str.lower().str.contains(title_lower, na=False)]
        if matches.empty:
            return []

    idx = matches.iloc[0]

    # Compute cosine similarity between this movie and all others
    cosine_sim = linear_kernel(tfidf_matrix[idx:idx+1], tfidf_matrix).flatten()

    # Get top similar movies (exclude itself)
    sim_scores = list(enumerate(cosine_sim))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:n+1]  # skip first (itself)

    movie_indices = [i[0] for i in sim_scores]
    results = df.iloc[movie_indices]

    return [_build_movie(row) for _, row in results.iterrows()]


def get_trending(page: int = 1, per_page: int = 20):
    """Get trending/popular movies."""
    sorted_df = df.sort_values("popularity", ascending=False)
    start = (page - 1) * per_page
    end = start + per_page
    subset = sorted_df.iloc[start:end]

    return [_build_movie(row) for _, row in subset.iterrows()]


def search_movies(query: str, limit: int = 20):
    """Search movies by title."""
    query_lower = query.lower().strip()
    mask = df["title"].str.lower().str.contains(query_lower, na=False)
    results = df[mask].head(limit)

    return [_build_movie(row) for _, row in results.iterrows()]


def get_poster_url(title: str) -> str:
    """Fetch movie poster URL from TMDB API."""
    if not TMDB_API_KEY:
        return ""
    try:
        resp = requests.get(
            TMDB_SEARCH_URL,
            params={"api_key": TMDB_API_KEY, "query": title},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results and results[0].get("poster_path"):
                return TMDB_IMG_BASE + results[0]["poster_path"]
    except Exception:
        pass
    return ""


def get_all_titles(limit: int = 50000):
    """Return all movie titles for autocomplete."""
    return df["title"].dropna().unique().tolist()[:limit]
