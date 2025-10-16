"""Test script: 3-day weather forecast for Bielsko-Biała, Poland."""
from time import sleep

from vibe2025.weather.open_meteo import OpenMeteoService


def main():
    """Fetch and display a 3-day forecast for Bielsko-Biała."""
    # Bielsko-Biała coordinates
    latitude = 49.8224
    longitude = 19.0469

    service = OpenMeteoService(timeout=30.0)
    n_days = 5
    print(f"Fetching {n_days}-day weather forecast for Bielsko-Biała, Poland...")
    print(f"Coordinates: {latitude}°N, {longitude}°E\n")

    try:
        forecasts = service.get_forecast(latitude, longitude, days=n_days)

        print("=" * 70)
        print(f"{'Date':<15} {'Min Temp':<12} {'Max Temp':<12} {'Precipitation'}")
        print("=" * 70)

        for forecast in forecasts:
            min_t, max_t, precip = forecast.as_tuple()
            print(f"{forecast.date!s:<15} {min_t:>8.1f}°C    {max_t:>8.1f}°C    {precip:>8.1f} mm")

        print("=" * 70)
        print(f"\nTotal forecasts retrieved: {len(forecasts)}")

        # Display as tuples
        print("\nAs tuples (min_temp, max_temp, precipitation):")
        for i, forecast in enumerate(forecasts, 1):
            print(f"Day {i}: {forecast.as_tuple()}")

    except ValueError as e:
        print(f"Validation error: {e}")
    except TimeoutError as e:
        print(f"Timeout: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
