"""Open-Meteo weather service implementation."""
import requests
from datetime import datetime
from typing import List

from vibe2025.weather.base import WeatherService
from vibe2025.weather.model import DayForecast


class OpenMeteoService(WeatherService):
    """Weather service using Open-Meteo API (no API key required)."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout: float = 30.0, timezone: str = "auto") -> None:
        """
        Initialize the service.

        Args:
            timeout: Request timeout in seconds
            timezone: Timezone for response (default: auto-detect)
        """
        self._timeout = timeout
        self._timezone = timezone
        self._session = requests.Session()

    def get_forecast(
            self,
            latitude: float,
            longitude: float,
            days: int,
    ) -> List[DayForecast]:
        """
        Fetch weather forecast from Open-Meteo API.

        Args:
            latitude: Latitude coordinate (-90..90)
            longitude: Longitude coordinate (-180..180)
            days: Number of days to forecast (1-16)

        Returns:
            List of DayForecast objects validated by Pydantic

        Raises:
            ValueError: If coordinates or days are invalid
            requests.HTTPError: If API request fails
        """
        if not (-90.0 <= latitude <= 90.0):
            raise ValueError(f"Invalid latitude: {latitude}")
        if not (-180.0 <= longitude <= 180.0):
            raise ValueError(f"Invalid longitude: {longitude}")
        if not (1 <= days <= 16):
            raise ValueError(f"Days must be between 1 and 16, got {days}")

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "forecast_days": days,
            "timezone": self._timezone,
        }

        try:
            response = self._session.get(
                self.BASE_URL,
                params=params,
                timeout=self._timeout
            )
            response.raise_for_status()
            data = response.json()
        except requests.Timeout:
            raise TimeoutError(f"Request timed out after {self._timeout}s")
        except requests.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")

        # Parse response
        daily = data.get("daily", {})
        dates = daily.get("time", []) or []
        max_temps = daily.get("temperature_2m_max", []) or []
        min_temps = daily.get("temperature_2m_min", []) or []
        precip = daily.get("precipitation_sum", []) or []

        if not (len(dates) == len(max_temps) == len(min_temps) == len(precip)):
            raise ValueError("Mismatched daily arrays in Open-Meteo response")

        forecasts: List[DayForecast] = []
        for i in range(len(dates)):
            # Parse ISO8601 date from daily.time (e.g., "2025-10-11")
            forecast_date = datetime.fromisoformat(dates[i]).date()

            # Pydantic validates the data automatically
            forecasts.append(
                DayForecast(
                    date=forecast_date,
                    min_temp=float(min_temps[i]),
                    max_temp=float(max_temps[i]),
                    precipitation_mm=float(precip[i] or 0.0),
                )
            )

        return forecasts

    def __del__(self):
        """Close the session on cleanup."""
        if hasattr(self, '_session'):
            self._session.close()
