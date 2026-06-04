from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
import structlog

from application.dto.audit_dto import AuditLogResponse, AuditLogListResponse
from application.use_cases.audit_use_cases import ListAuditLogsUseCase, GetAuditLogUseCase
from domain.repositories import AuditLogRepository

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/logs", response_model=AuditLogListResponse)
async def list_logs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
):
    audit_repo: AuditLogRepository = request.app.state.audit_repo
    use_case = ListAuditLogsUseCase(audit_repo)
    logs, total = await use_case.execute(
        skip=skip, limit=limit, event_type=event_type,
        user_id=user_id, from_date=from_date, to_date=to_date,
    )
    return AuditLogListResponse(
        items=[
            AuditLogResponse(
                id=log.id or "",
                event_type=log.event_type,
                user_id=log.user_id,
                user_email=log.user_email,
                resource=log.resource,
                action=log.action,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                metadata=log.metadata,
                timestamp=log.timestamp,
            )
            for log in logs
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_log(request: Request, log_id: str):
    audit_repo: AuditLogRepository = request.app.state.audit_repo
    use_case = GetAuditLogUseCase(audit_repo)
    log = await use_case.execute(log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return AuditLogResponse(
        id=log.id or "",
        event_type=log.event_type,
        user_id=log.user_id,
        user_email=log.user_email,
        resource=log.resource,
        action=log.action,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        metadata=log.metadata,
        timestamp=log.timestamp,
    )


@router.get("/stats")
async def get_stats(request: Request):
    audit_repo: AuditLogRepository = request.app.state.audit_repo
    stats = await audit_repo.get_stats()
    return stats
