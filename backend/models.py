"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional, List


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class MovieOut(BaseModel):
    title: str
    overview: Optional[str] = ""
    genres: Optional[str] = ""
    tagline: Optional[str] = ""
    vote_average: Optional[float] = 0.0
    popularity: Optional[float] = 0.0
    poster_url: Optional[str] = None


class RecommendationResponse(BaseModel):
    source_movie: str
    recommendations: List[MovieOut]
