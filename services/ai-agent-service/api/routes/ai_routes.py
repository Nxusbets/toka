from fastapi import APIRouter, HTTPException, Request
import structlog

from application.dto.ai_dto import (
    QueryRequest, QueryResponse, IngestRequest,
    EvaluationMetrics, ReportRequest, ReportResponse,
)
from application.use_cases.ai_use_cases import (
    QueryUseCase, IngestDocumentUseCase, ReportUseCase, EvaluateUseCase,
)
from domain.repositories import VectorRepository
from infrastructure.message_queue import RabbitMQPublisher

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(request: Request, body: QueryRequest):
    use_case: QueryUseCase = request.app.state.query_use_case
    if use_case is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    result = await use_case.execute(
        user_query=body.query,
        user_id=body.user_id,
        collection=body.collection,
    )

    mq: RabbitMQPublisher = request.app.state.mq_publisher
    await mq.publish(
        "ai.query.completed",
        {
            "event_type": "ai.query.completed",
            "user_id": body.user_id,
            "resource": "ai/query",
            "action": "query",
            "metadata": {
                "latency_ms": result.latency_ms,
                "tokens_used": result.tokens_used,
                "cost": result.cost,
            },
        },
    )

    return QueryResponse(
        answer=result.response,
        context_docs=result.context_docs,
        latency_ms=result.latency_ms,
        tokens_used=result.tokens_used,
        cost=result.cost,
        model="gpt-4o-mini",
    )


@router.post("/report", response_model=ReportResponse)
async def generate_report(request: Request, body: ReportRequest):
    use_case: ReportUseCase = request.app.state.report_use_case
    if use_case is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    report = await use_case.execute(
        user_id=body.user_id,
        period=body.period,
        report_type=body.report_type,
    )
    return ReportResponse(
        report=report,
        user_id=body.user_id,
    )


@router.post("/ingest", response_model=dict)
async def ingest_documents(request: Request, body: IngestRequest):
    use_case: IngestDocumentUseCase = request.app.state.ingest_use_case
    if use_case is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    count = await use_case.execute(
        documents=body.documents,
        collection=body.collection,
    )
    return {"status": "ok", "documents_ingested": count}


@router.get("/evaluate", response_model=EvaluationMetrics)
async def evaluate(request: Request):
    use_case: EvaluateUseCase = request.app.state.evaluate_use_case
    if use_case is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    metrics = await use_case.execute()
    return EvaluationMetrics(**metrics)


@router.get("/collections", response_model=list[str])
async def list_collections(request: Request):
    vector_repo: VectorRepository = request.app.state.vector_repo
    if vector_repo is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    collections = await vector_repo.list_collections()
    return collections
