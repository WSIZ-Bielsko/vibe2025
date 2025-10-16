"""Example: Using Windy service for Bielsko-Biała."""
from vibe2025.weather.windy_service import WindyService


def main():
    # Get API key from https://api.windy.com/keys
    api_key = "YOUR_WINDY_API_KEY"

    service = WindyService(api_key=api_key, model="gfs")

    # Bielsko-Biała coordinates
    forecasts = service.get_forecast(
        latitude=49.8224,
        longitude=19.0469,
        days=3
    )

    for forecast in forecasts:
        print(f"{forecast.date}: {forecast.as_tuple()}")


if __name__ == "__main__":
    main()
