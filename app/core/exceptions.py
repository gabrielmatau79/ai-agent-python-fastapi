from __future__ import annotations

from fastapi import HTTPException, status


class ApplicationError(Exception):
    """Base application exception."""


class ConfigurationError(ApplicationError):
    """Raised for invalid application configuration."""


class ProviderUnavailableError(ApplicationError):
    """Raised when an optional provider cannot be used."""


class ValidationApplicationError(ApplicationError):
    """Raised for internal validation issues."""


class ExternalServiceError(ApplicationError):
    """Raised for provider or network failures."""


def to_http_exception(error: Exception) -> HTTPException:
    if isinstance(error, ValidationApplicationError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    if isinstance(error, ConfigurationError):
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error))
    if isinstance(error, ProviderUnavailableError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))
    if isinstance(error, ExternalServiceError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error))
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error."
    )
