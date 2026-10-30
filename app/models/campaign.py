from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class CampaignInfluencer(BaseModel):
    handle: str
    agreed_fee: float
    deliverables: str
    status: str = "Contracted"  # Proposed, Contracted, Completed

class CampaignKPIs(BaseModel):
    target_impressions: int
    achieved_impressions: int
    target_engagement: int
    achieved_engagement: int
    calculated_roi: float

class CampaignCreate(BaseModel):
    brand_name: str
    campaign_title: str
    target_niche: str
    total_budget: float
    spent_budget: float = 0.0
    start_date: datetime
    end_date: datetime
    status: str = "Active"  # Planning, Active, Completed, Paused
    assigned_influencers: List[CampaignInfluencer] = []
    performance_kpis: CampaignKPIs

class CampaignResponse(CampaignCreate):
    id: str
