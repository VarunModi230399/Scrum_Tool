from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.platform.config import get_settings
from src.platform.health import router as health_router
from src.platform.logging import configure_logging
from src.shared_kernel.errors import AppError

settings = get_settings()
configure_logging()

app = FastAPI(title="Scrum Tool API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


app.include_router(health_router)

# Module routers are mounted here as each module's API layer is implemented,
# e.g. app.include_router(identity_router, prefix="/api/v1")
