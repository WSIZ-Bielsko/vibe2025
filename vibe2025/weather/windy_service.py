"""Windy.com Point Forecast API service implementation."""
import requests
from datetime import datetime, timedelta
from typing import List

from vibe2025.weather.base import WeatherService
from vibe2025.weather.model import DayForecast


class WindyService(WeatherService):
    """Weather service using Windy.com Point Forecast API (requires API key)."""

    BASE_URL = "https://api.windy.com/api/point-forecast/v2"

    def __init__(self, api_key: str, model: str = "gfs", timeout: float = 30.0) -> None:
        """
        Initialize the Windy service.

        Args:
            api_key: Windy Point Forecast API key (get at https://api.windy.com/keys)
            model: Weather model (gfs, iconEu, arome, namConus, etc.)
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValueError("Windy API key is required")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._session = requests.Session()

    def get_forecast(
            self,
            latitude: float,
            longitude: float,
            days: int,
    ) -> List[DayForecast]:
        """
        Fetch weather forecast from Windy Point Forecast API.

        Args:
            latitude: Latitude coordinate (-90..90)
            longitude: Longitude coordinate (-180..180)
            days: Number of days to forecast

        Returns:
            List of DayForecast objects validated by Pydantic

        Raises:
            ValueError: If coordinates are invalid
            requests.HTTPError: If API request fails
        """
        if not (-90.0 <= latitude <= 90.0):
            raise ValueError(f"Invalid latitude: {latitude}")
        if not (-180.0 <= longitude <= 180.0):
            raise ValueError(f"Invalid longitude: {longitude}")

        # Windy API request body
        payload = {
            "lat": round(latitude, 2),  # Windy rounds to 2 decimals
            "lon": round(longitude, 2),
            "model": self._model,
            "parameters": ["temp", "precip"],
            "key": self._api_key
        }

        try:
            response = self._session.post(
                self.BASE_URL,
                json=payload,
                timeout=self._timeout
            )
            response.raise_for_status()
            data = response.json()
        except requests.Timeout:
            raise TimeoutError(f"Request timed out after {self._timeout}s")
        except requests.RequestException as e:
            raise RuntimeError(f"Windy API request failed: {e}")

        # Parse Windy response
        # Windy returns timestamps (ts) in milliseconds and hourly data
        timestamps = data.get("ts", [])
        temps = data.get("temp-surface", [])  # Temperature at surface level
        precip = data.get("precip-surface", [])  # Precipitation at surface

        if not timestamps or not temps:
            raise ValueError("Invalid response from Windy API")

        # Group hourly data into daily forecasts
        forecasts = self._aggregate_to_daily(timestamps, temps, precip, days)

        return forecasts

    def _aggregate_to_daily(
            self,
            timestamps: List[int],
            temps: List[float],
            precip: List[float],
            days: int
    ) -> List[DayForecast]:
        """
        Aggregate hourly Windy data into daily min/max/precipitation.

        Args:
            timestamps: Unix timestamps in milliseconds
            temps: Hourly temperature values (Celsius)
            precip: Hourly precipitation values (mm)
            days: Number of days to return

        Returns:
            List of DayForecast objects
        """
        daily_data = {}

        for i, ts_ms in enumerate(timestamps):
            # Convert milliseconds to datetime
            dt = datetime.fromtimestamp(ts_ms / 1000.0)
            date_key = dt.date()

            temp = temps[i] if i < len(temps) else None
            prec = precip[i] if i < len(precip) else 0.0

            if temp is None:
                continue

            if date_key not in daily_data:
                daily_data[date_key] = {
                    'temps': [],
                    'precip': 0.0
                }

            daily_data[date_key]['temps'].append(temp)
            daily_data[date_key]['precip'] += prec or 0.0

        # Convert to DayForecast objects
        forecasts: List[DayForecast] = []
        sorted_dates = sorted(daily_data.keys())

        for date_key in sorted_dates[:days]:
            day_data = daily_data[date_key]
            temps_list = day_data['temps']

            if not temps_list:
                continue

            forecasts.append(
                DayForecast(
                    date=date_key,
                    min_temp=float(min(temps_list)),
                    max_temp=float(max(temps_list)),
                    precipitation_mm=float(day_data['precip'])
                )
            )

        return forecasts

    def __del__(self):
        """Close the session on cleanup."""
        if hasattr(self, '_session'):
            self._session.close()
