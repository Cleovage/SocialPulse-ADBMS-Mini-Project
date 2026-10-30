from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]

class PostLocation(BaseModel):
    type: str = "Point"
    coordinates: List[float]
    place_name: Optional[str] = None

class PostMetrics(BaseModel):
    likes: int
    comments: int
    shares: int
    saves: int
    impressions: int
    reach: int
    viral_score: float

class PostSentiment(BaseModel):
    label: str  # Positive, Neutral, Negative
    score: float  # -1.0 to +1.0
    emotions: Optional[Dict[str, float]] = None

class PostCreate(BaseModel):
    influencer_handle: str
    influencer_id: Optional[str] = None
    platform: str
    content: str
    hashtags: List[str]
    mentions: List[str] = []
    post_type: str  # Video, Reel, Image, Carousel, Tweet
    metrics: PostMetrics
    sentiment: PostSentiment
    location: Optional[PostLocation] = None
    published_at: Optional[datetime] = None

class PostResponse(PostCreate):
    id: str
