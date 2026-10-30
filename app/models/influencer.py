from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]

class Location(BaseModel):
    city: str
    country: str
    coordinates: Optional[GeoPoint] = None

class Demographics(BaseModel):
    gender: Dict[str, float]
    age_brackets: Dict[str, float]
    top_countries: List[Dict[str, Any]]

class InfluencerMetrics(BaseModel):
    followers_count: int
    following_count: int
    total_posts: int
    engagement_rate: float
    avg_likes: int
    avg_comments: int
    credibility_score: int
    fake_followers_pct: float

class InfluencerCreate(BaseModel):
    handle: str
    name: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    niche: str
    platform_primary: str
    tier: str
    metrics: InfluencerMetrics
    audience_demographics: Demographics
    collaboration_rates: Dict[str, float]
    network: Optional[Dict[str, List[str]]] = None
    location: Location
    location_geo: Optional[GeoPoint] = None

class InfluencerResponse(InfluencerCreate):
    id: str
    created_at: Optional[str] = None
