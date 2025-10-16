"""Data models for weather forecasts."""
from datetime import date
from pydantic import BaseModel, Field


class DayForecast(BaseModel):
    """Daily weather forecast data."""
    date: date
    min_temp: float = Field(..., description="Minimum temperature in Celsius")
    max_temp: float = Field(..., description="Maximum temperature in Celsius")
    precipitation_mm: float = Field(..., ge=0.0, description="Precipitation in millimeters")

    def as_tuple(self) -> tuple[float, float, float]:
        """Return forecast as (min_temp, max_temp, precipitation_mm)."""
        return (self.min_temp, self.max_temp, self.precipitation_mm)
