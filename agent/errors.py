"""
J.A.V.I.S. Custom Exceptions & Error Handling
"""
from fastapi import HTTPException, status
from typing import Optional


class JAVISException(Exception):
    """Base exception for J.A.V.I.S."""
    pass


class AuthenticationError(JAVISException):
    """Raised when authentication fails"""
    
    def __init__(self, detail: str = "Authentication failed"):
        self.detail = detail
        super().__init__(detail)
    
    def to_http_exception(self):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=self.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(JAVISException):
    """Raised when user lacks permission"""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        self.detail = detail
        super().__init__(detail)
    
    def to_http_exception(self):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=self.detail,
        )


class NotFoundError(JAVISException):
    """Raised when resource not found"""
    
    def __init__(self, resource: str, identifier: str):
        self.detail = f"{resource} not found: {identifier}"
        super().__init__(self.detail)
    
    def to_http_exception(self):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=self.detail,
        )


class ValidationError(JAVISException):
    """Raised when input validation fails"""
    
    def __init__(self, detail: str = "Validation failed"):
        self.detail = detail
        super().__init__(detail)
    
    def to_http_exception(self):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=self.detail,
        )


class RateLimitError(JAVISException):
    """Raised when rate limit exceeded"""
    
    def __init__(self, detail: str = "Too many requests"):
        self.detail = detail
        super().__init__(detail)
    
    def to_http_exception(self):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=self.detail,
            headers={"Retry-After": "60"},
        )


class ExternalServiceError(JAVISException):
    """Raised when external service fails (email, SMS, AI)"""
    
    def __init__(self, service: str, detail: str):
        self.detail = f"{service} error: {detail}"
        super().__init__(self.detail)
    
    def to_http_exception(self):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=self.detail,
        )
