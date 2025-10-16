from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class ServiceTarget(BaseModel):
    """Model for service target configuration."""
    host: str = Field(..., description="IP address or domain name")
    port: int = Field(..., ge=1, le=65535, description="Port number")


class CheckResult(BaseModel):
    """Model for availability check result."""
    host: str
    port: int
    status: Literal["available", "unavailable", "error"]
    timestamp: datetime
    error_message: str | None = None
    response_time_ms: float | None = None


class MonitorResults(BaseModel):
    """Container for all check results."""
    check_timestamp: datetime
    results: list[CheckResult]
