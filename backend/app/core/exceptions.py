"""
Global FastAPI exception handlers.

Register these on the app instance inside app/main.py.
"""

import traceback

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    tb = traceback.format_exc()
    print(f"[Unhandled Error] {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )
