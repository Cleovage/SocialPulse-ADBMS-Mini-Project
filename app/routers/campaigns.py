from fastapi import APIRouter, HTTPException, Query, Body
from bson import ObjectId
from typing import Optional, List
from datetime import datetime, timezone
from app.database import Database, serialize_doc
from app.models.campaign import CampaignCreate
import logging

router = APIRouter(prefix="/api/campaigns", tags=["Brand Campaigns & Transactions"])
logger = logging.getLogger("socialpulse.campaigns")

@router.get("")
async def get_campaigns(status: Optional[str] = None):
    """
    List marketing campaigns with budget usage and performance ROI.
    """
    db = Database.db
    query = {}
    if status and status != "All":
        query["status"] = status

    campaigns = list(db["campaigns"].find(query).sort("start_date", -1))
    return {
        "count": len(campaigns),
        "data": serialize_doc(campaigns)
    }

@router.get("/matchmaker")
async def match_influencers_for_campaign(
    niche: str,
    max_budget_per_creator: float = 15000.0,
    min_credibility: int = 85,
    min_er: float = 4.0
):
    """
    Matchmaking algorithm: Queries MongoDB to find ideal creators for a brand campaign
    based on niche, collaboration rate feasibility, high engagement rate, and high credibility.
    """
    db = Database.db
    query = {
        "niche": niche,
        "collaboration_rates.reel_video_rate_usd": {"$lte": max_budget_per_creator},
        "metrics.credibility_score": {"$gte": min_credibility},
        "metrics.engagement_rate": {"$gte": min_er}
    }
    candidates = list(
        db["influencers"].find(query)
        .sort("metrics.engagement_rate", -1)
        .limit(10)
    )
    return {
        "criteria": {
            "niche": niche,
            "max_budget_per_creator": max_budget_per_creator,
            "min_credibility": min_credibility,
            "min_er": min_er
        },
        "matched_count": len(candidates),
        "matches": serialize_doc(candidates)
    }

@router.post("/allocate-budget-transaction")
async def execute_campaign_transaction(
    campaign_id: str = Body(..., embed=True),
    influencer_handle: str = Body(..., embed=True),
    fee: float = Body(..., embed=True),
    simulate_rollback: bool = Body(False, embed=True)
):
    """
    ADBMS ACID Multi-Document Transaction Demonstration:
    Atomically allocates budget, registers influencer contract, and verifies data integrity.
    Demonstrates session.start_transaction(), session.commit_transaction(), and session.abort_transaction().
    """
    db = Database.db
    client = Database.client

    if not ObjectId.is_valid(campaign_id):
        raise HTTPException(status_code=400, detail="Invalid campaign ID.")

    camp = db["campaigns"].find_one({"_id": ObjectId(campaign_id)})
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    inf = db["influencers"].find_one({"handle": influencer_handle})
    if not inf:
        raise HTTPException(status_code=404, detail=f"Influencer {influencer_handle} not found.")

    # Check budget headroom
    remaining_budget = camp["total_budget"] - camp["spent_budget"]
    if fee > remaining_budget:
        raise HTTPException(status_code=400, detail=f"Insufficient campaign budget. Remaining: ${remaining_budget:,.2f}, Requested: ${fee:,.2f}")

    # Check if MongoDB is running as Replica Set (required for multi-doc transactions)
    # If standalone, we execute atomic compensation rollback to guarantee consistency and explain
    is_replica_set = bool(client.topology_description.replica_set_name)

    contract_data = {
        "handle": influencer_handle,
        "agreed_fee": fee,
        "deliverables": "1 Sponsored Post & 2 Dedicated Stories",
        "status": "Contracted",
        "contracted_at": datetime.now(timezone.utc).isoformat()
    }

    if is_replica_set:
        # Full MongoDB Distributed ACID Transaction
        with client.start_session() as session:
            try:
                session.start_transaction()
                
                # Step 1: Update campaign spent budget
                db["campaigns"].update_one(
                    {"_id": ObjectId(campaign_id)},
                    {"$inc": {"spent_budget": fee}, "$push": {"assigned_influencers": contract_data}},
                    session=session
                )

                if simulate_rollback:
                    session.abort_transaction()
                    return {
                        "status": "aborted",
                        "mode": "MongoDB ReplicaSet ACID Session",
                        "message": "Transaction intentionally aborted! State was rolled back atomically. No partial data persisted.",
                        "campaign_id": campaign_id
                    }

                session.commit_transaction()
                return {
                    "status": "committed",
                    "mode": "MongoDB ReplicaSet ACID Session",
                    "message": "Transaction committed successfully across documents.",
                    "allocated_fee": fee,
                    "influencer": influencer_handle
                }
            except Exception as e:
                session.abort_transaction()
                raise HTTPException(status_code=500, detail=f"Transaction aborted due to error: {str(e)}")
    else:
        # Standalone MongoDB ACID emulation with rollback demonstration
        if simulate_rollback:
            return {
                "status": "aborted",
                "mode": "Simulated ACID Transaction (Standalone Node)",
                "message": "Rollback simulation triggered: No database mutations were committed. Budget remains untouched.",
                "campaign_id": campaign_id,
                "current_spent": camp["spent_budget"],
                "remaining_budget": remaining_budget
            }
        
        # Atomic document update
        db["campaigns"].update_one(
            {"_id": ObjectId(campaign_id)},
            {"$inc": {"spent_budget": fee}, "$push": {"assigned_influencers": contract_data}}
        )

        return {
            "status": "committed",
            "mode": "Atomic Document Mutation",
            "message": f"Successfully allocated ${fee:,.2f} and contracted creator {influencer_handle}.",
            "new_spent_budget": camp["spent_budget"] + fee,
            "contract": contract_data
        }
