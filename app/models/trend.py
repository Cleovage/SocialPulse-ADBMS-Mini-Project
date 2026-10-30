from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class HourlyVolume(BaseModel):
    hour: str
    volume: int

class SentimentSummary(BaseModel):
    positive_pct: float
    neutral_pct: float
    negative_pct: float

class TrendCreate(BaseModel):
    hashtag: str
    topic: str
    category: str
    volume_24h: int
    velocity_score: float  # e.g., +245.5%
    viral_index: float     # 0-100
    sentiment_summary: SentimentSummary
    platform_breakdown: Dict[str, int]
    lifecycle_status: str  # Emerging, Surging, Peaked, Declining
    top_influencer_handles: List[str]
    hourly_history: List[HourlyVolume]
    peak_time: Optional[datetime] = None

class TrendResponse(TrendCreate):
    id: str
