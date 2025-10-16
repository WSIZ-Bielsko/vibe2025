"""Abstract base class for weather services."""
from abc import ABC, abstractmethod
from typing import List
from vibe2025.weather.model import DayForecast


class WeatherService(ABC):
    """Abstract weather service interface."""

    @abstractmethod
    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int,
    ) -> List[DayForecast]:
        """
        Fetch weather forecast for N days.

        Args:
            latitude: Latitude coordinate (-90..90)
            longitude: Longitude coordinate (-180..180)
            days: Number of days to forecast

        Returns:
            List of DayForecast objects
        """
        raise NotImplementedError

