import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db import ping
from app.errors import AppError, app_error_handler, error_body
from app.routes import access_routes, auth_routes, chat_routes, content_routes, stretch_routes
from app.schemas import HealthResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("campusgpt")

app = FastAPI(title="CampusGPT API", version="1.0.0")
app.add_exception_handler(AppError, app_error_handler)
for router in (
    auth_routes.router,
    chat_routes.router,
    content_routes.router,
    stretch_routes.router,
    access_routes.router,
):
    app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(part) for part in first.get("loc", [])[1:]) or "request"
    message = f"Invalid {field}: {first.get('msg', 'bad value')}"
    return JSONResponse(error_body("invalid_request", message), status_code=400)


@app.exception_handler(Exception)
async def unexpected_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error", exc_info=exc)
    return JSONResponse(
        error_body("internal_error", "Something went wrong. Please try again."), 500
    )


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health() -> HealthResponse:
    """App and database status."""
    database = ping()
    return HealthResponse(status="ok" if database else "degraded", database=database)
