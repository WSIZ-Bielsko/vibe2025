import asyncio
import json
from pathlib import Path
from datetime import datetime
from vibe2025.uptime_checker.config import AppConfig
from vibe2025.uptime_checker.checker import check_all_services
from vibe2025.uptime_checker.models import MonitorResults


async def monitor_services(config: AppConfig):
    """Main monitoring loop."""

    # Load services from the config file
    services = config.load_services()
    print(f"Loaded {len(services)} services to monitor")
    print(f"Check interval: {config.check_interval_seconds}s")
    print(f"Connection timeout: {config.connection_timeout_seconds}s\n")

    while True:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running checks...")

        # Check all services
        results = await check_all_services(
            services,
            config.connection_timeout_seconds
        )

        # Create results container
        monitor_results = MonitorResults(
            check_timestamp=datetime.now(),
            results=results
        )

        # Save to JSON file
        results_path = Path(config.results_file)
        with open(results_path, 'w', encoding='utf-8') as f:
            f.write(monitor_results.model_dump_json(indent=2))

        # Print summary
        available = sum(1 for r in results if r.status == "available")
        print(f"Results: {available}/{len(results)} services available")
        print(f"Saved to: {results_path}\n")

        # Wait for the next check
        await asyncio.sleep(config.check_interval_seconds)


def main():
    """Entry point for the application."""
    config = AppConfig()

    try:
        asyncio.run(monitor_services(config))
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
