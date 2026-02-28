"""FastAPI main application — Movie Recommendation Web App."""

import os
import requests as http_requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from backend.database import init_db, get_user_by_username, get_user_by_email, create_user
from backend.models import UserRegister, UserLogin, Token, MovieOut, RecommendationResponse
from backend.auth import hash_password, verify_password, create_access_token, get_current_user
from backend import recommender


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    init_db()
    recommender.load_model()
    yield


app = FastAPI(title="🎬 Movie Recommender", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


# ─────────────────────────── Auth Routes ───────────────────────────

@app.post("/api/register")
async def register(user: UserRegister):
    """Register a new user."""
    if len(user.username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(user.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if get_user_by_username(user.username):
        raise HTTPException(409, "Username already exists")
    if get_user_by_email(user.email):
        raise HTTPException(409, "Email already registered")

    hashed = hash_password(user.password)
    success = create_user(user.username, user.email, hashed)
    if not success:
        raise HTTPException(500, "Failed to create user")

    return {"message": "Account created successfully! Please log in."}


@app.post("/api/login", response_model=Token)
async def login(user: UserLogin):
    """Login and receive a JWT token."""
    db_user = get_user_by_username(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(401, "Invalid username or password")

    token = create_access_token(data={"sub": db_user["username"]})
    return Token(access_token=token, username=db_user["username"])


# ─────────────────────────── Movie Routes ──────────────────────────

@app.get("/api/movies/trending")
async def trending_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    _user: str = Depends(get_current_user),
):
    """Get trending/popular movies."""
    movies = recommender.get_trending(page=page, per_page=per_page)
    return {"movies": movies, "page": page}


@app.get("/api/movies/search")
async def search_movies(
    q: str = Query(..., min_length=1),
    _user: str = Depends(get_current_user),
):
    """Search movies by title."""
    movies = recommender.search_movies(q)
    return {"movies": movies, "query": q}


@app.get("/api/movies/recommend/{title:path}")
async def recommend_movies(
    title: str,
    n: int = Query(12, ge=1, le=30),
    _user: str = Depends(get_current_user),
):
    """Get movie recommendations based on a title."""
    movies = recommender.get_recommendations(title, n=n)
    if not movies:
        raise HTTPException(404, f"No recommendations found for '{title}'")
    return {"source_movie": title, "recommendations": movies}


@app.get("/api/movies/poster")
async def movie_poster(
    title: str = Query(...),
    _user: str = Depends(get_current_user),
):
    """Get TMDB poster URL for a movie."""
    url = recommender.get_poster_url(title)
    return {"title": title, "poster_url": url}


@app.get("/api/movies/titles")
async def all_titles(_user: str = Depends(get_current_user)):
    """Get all movie titles for autocomplete."""
    titles = recommender.get_all_titles()
    return {"titles": titles}


@app.get("/api/tmdb-key")
async def tmdb_key(_user: str = Depends(get_current_user)):
    """Return the TMDB API key for client-side poster fetching."""
    return {"key": recommender.TMDB_API_KEY}


@app.get("/api/img-proxy")
async def img_proxy(url: str = Query(...)):
    """Proxy TMDB images to bypass network blocks on image.tmdb.org."""
    if not url.startswith("https://image.tmdb.org/"):
        raise HTTPException(400, "Only TMDB image URLs are allowed")
    try:
        r = http_requests.get(url, timeout=10)
        if r.status_code == 200:
            content_type = r.headers.get("content-type", "image/jpeg")
            return Response(content=r.content, media_type=content_type,
                           headers={"Cache-Control": "public, max-age=86400"})
        raise HTTPException(r.status_code, "Failed to fetch image")
    except http_requests.exceptions.Timeout:
        raise HTTPException(504, "Image fetch timed out")
    except Exception as e:
        raise HTTPException(502, str(e))


# ─────────────────────────── Frontend Serving ──────────────────────

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))


# Serve static assets (CSS, JS, images)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
