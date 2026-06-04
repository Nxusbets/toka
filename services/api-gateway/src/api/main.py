import logging

import httpx
import structlog
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.config import Settings

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

settings = Settings()

app = FastAPI(title="API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROUTES: dict[str, str] = {
    "/api/v1/auth": settings.auth_service_url,
    "/api/v1/users": settings.user_service_url,
    "/api/v1/roles": settings.user_service_url,
    "/api/v1/audit": settings.audit_service_url,
    "/api/v1/ai": settings.ai_agent_service_url,
}


@app.get("/health")
async def health():
    statuses: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        endpoints = [
            ("auth", f"{settings.auth_service_url}/health"),
            ("users", f"{settings.user_service_url}/health"),
            ("audit", f"{settings.audit_service_url}/health"),
            ("ai", f"{settings.ai_agent_service_url}/health"),
        ]
        for name, url in endpoints:
            try:
                resp = await client.get(url)
                statuses[name] = "up" if resp.status_code == 200 else "degraded"
            except Exception:
                statuses[name] = "down"
    return {"status": "ok", "service": "api-gateway", "upstreams": statuses}


def get_upstream(request: Request) -> str | None:
    path = request.url.path
    if path == "/health":
        return None
    for prefix, upstream in sorted(ROUTES.items(), key=lambda x: -len(x[0])):
        if path.startswith(prefix):
            return upstream + path
    return None


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def proxy(request: Request, path: str):
    upstream_url = get_upstream(request)
    if upstream_url is None:
        return JSONResponse(status_code=404, content={"detail": "Route not found"})

    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=upstream_url,
                headers=headers,
                content=body,
                params=request.query_params,
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except httpx.RequestError as e:
            await logger.aerror("proxy_error", path=path, upstream=upstream_url, error=str(e))
            return JSONResponse(
                status_code=502,
                content={"detail": f"Upstream service error: {str(e)}"},
            )
