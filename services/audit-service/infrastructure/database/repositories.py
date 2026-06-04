from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.audit_log import AuditLog
from domain.repositories import AuditLogRepository


class MongoAuditLogRepository(AuditLogRepository):
    def __init__(self, database: AsyncIOMotorDatabase):
        self._collection = database["audit_logs"]

    async def create(self, log: AuditLog) -> AuditLog:
        doc = {
            "event_type": log.event_type,
            "user_id": log.user_id,
            "user_email": log.user_email,
            "resource": log.resource,
            "action": log.action,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "metadata": log.metadata,
            "timestamp": log.timestamp,
        }
        result = await self._collection.insert_one(doc)
        log.id = str(result.inserted_id)
        return log

    async def find_by_id(self, log_id: str) -> Optional[AuditLog]:
        doc = await self._collection.find_one({"_id": ObjectId(log_id)})
        if doc is None:
            return None
        return self._doc_to_entity(doc)

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> tuple[list[AuditLog], int]:
        query: dict[str, Any] = {}
        if event_type:
            query["event_type"] = event_type
        if user_id:
            query["user_id"] = user_id
        if from_date or to_date:
            query["timestamp"] = {}
            if from_date:
                query["timestamp"]["$gte"] = datetime.fromisoformat(from_date)
            if to_date:
                query["timestamp"]["$lte"] = datetime.fromisoformat(to_date)

        total = await self._collection.count_documents(query)
        cursor = self._collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_entity(d) for d in docs], total

    async def get_stats(self) -> dict:
        total = await self._collection.count_documents({})
        pipeline = [{"$group": {"_id": "$event_type", "count": {"$sum": 1}}}]
        by_event_type = await self._collection.aggregate(pipeline).to_list(length=100)
        event_type_counts = {item["_id"]: item["count"] for item in by_event_type}

        date_pipeline = [
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        by_day = await self._collection.aggregate(date_pipeline).to_list(length=365)
        day_counts = [{"date": item["_id"], "count": item["count"]} for item in by_day]

        return {"total": total, "by_event_type": event_type_counts, "by_day": day_counts}

    def _doc_to_entity(self, doc: dict) -> AuditLog:
        return AuditLog(
            id=str(doc["_id"]),
            event_type=doc.get("event_type", ""),
            user_id=doc.get("user_id"),
            user_email=doc.get("user_email"),
            resource=doc.get("resource", ""),
            action=doc.get("action", ""),
            ip_address=doc.get("ip_address"),
            user_agent=doc.get("user_agent"),
            metadata=doc.get("metadata", {}),
            timestamp=doc.get("timestamp", datetime.utcnow()),
        )
