import json
from pathlib import Path
from datetime import datetime
from typing import List
from vibe2025.uptime_checker.models import CheckResult


class UptimeBrowser:
    """Browser for analyzing uptime data from results file."""

    def __init__(self, results_file: str = "results.json"):
        """Initialize browser with results file path."""
        self.results_file = Path(results_file)

    def load_all_results(self) -> List[CheckResult]:
        """Load all historical results from JSON file."""
        if not self.results_file.exists():
            raise FileNotFoundError(f"Results file not found: {self.results_file}")

        all_results = []

        # Note: This assumes results.json is continuously appended or you keep history
        # For simplicity, we'll read the current snapshot
        with open(self.results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Parse results
        for result_data in data.get("results", []):
            result = CheckResult(**result_data)
            all_results.append(result)

        return all_results

    def calculate_uptime(
            self,
            host: str,
            port: int,
            from_datetime: datetime,
            to_datetime: datetime,
            results: List[CheckResult]
    ) -> dict:
        """
        Calculate uptime statistics for a specific service in a time range.

        Args:
            host: Service host/IP
            port: Service port
            from_datetime: Start of time range
            to_datetime: End of time range
            results: List of all check results

        Returns:
            Dictionary with uptime statistics
        """
        # Filter results for this service and time range
        filtered = [
            r for r in results
            if r.host == host
               and r.port == port
               and from_datetime <= r.timestamp <= to_datetime
        ]

        if not filtered:
            return {
                "host": host,
                "port": port,
                "from": from_datetime.isoformat(),
                "to": to_datetime.isoformat(),
                "total_checks": 0,
                "available_checks": 0,
                "unavailable_checks": 0,
                "error_checks": 0,
                "uptime_percentage": 0.0,
                "avg_response_time_ms": None
            }

        # Count statuses
        available = sum(1 for r in filtered if r.status == "available")
        unavailable = sum(1 for r in filtered if r.status == "unavailable")
        error = sum(1 for r in filtered if r.status == "error")
        total = len(filtered)

        # Calculate uptime percentage
        uptime_pct = (available / total * 100) if total > 0 else 0.0

        # Calculate average response time
        response_times = [r.response_time_ms for r in filtered if r.response_time_ms is not None]
        avg_response = sum(response_times) / len(response_times) if response_times else None

        return {
            "host": host,
            "port": port,
            "from": from_datetime.isoformat(),
            "to": to_datetime.isoformat(),
            "total_checks": total,
            "available_checks": available,
            "unavailable_checks": unavailable,
            "error_checks": error,
            "uptime_percentage": round(uptime_pct, 2),
            "avg_response_time_ms": round(avg_response, 2) if avg_response else None
        }


def parse_datetime_input(prompt: str) -> datetime:
    """Parse datetime from user input in ISO format."""
    while True:
        try:
            user_input = input(prompt)
            # Support ISO 8601 format: YYYY-MM-DD HH:MM:SS or YYYY-MM-DDTHH:MM:SS
            return datetime.fromisoformat(user_input)
        except ValueError:
            print("Invalid format. Use ISO format: YYYY-MM-DD HH:MM:SS or YYYY-MM-DDTHH:MM:SS")


def main():
    """Interactive uptime browser."""
    print("=== Uptime Browser ===\n")

    # Initialize browser
    results_file = input("Results file path (default: results.json): ").strip()
    if not results_file:
        results_file = "results.json"

    try:
        browser = UptimeBrowser(results_file)
        results = browser.load_all_results()
        print(f"Loaded {len(results)} check results\n")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"Error loading results: {e}")
        return

    # Get service details
    host = input("Service host/IP: ").strip()
    port_str = input("Service port: ").strip()

    try:
        port = int(port_str)
    except ValueError:
        print("Error: Port must be a number")
        return

    # Get time range
    print("\nEnter time range (ISO format: YYYY-MM-DD HH:MM:SS), eg 2025-10-15 00:00:00")
    from_dt = parse_datetime_input("From datetime: ")
    to_dt = parse_datetime_input("To datetime: ")

    if from_dt >= to_dt:
        print("Error: 'From' datetime must be before 'To' datetime")
        return

    # Calculate uptime
    stats = browser.calculate_uptime(host, port, from_dt, to_dt, results)

    # Display results
    print("\n" + "=" * 50)
    print("UPTIME STATISTICS")
    print("=" * 50)
    print(f"Service: {stats['host']}:{stats['port']}")
    print(f"Period: {stats['from']} to {stats['to']}")
    print(f"\nTotal checks: {stats['total_checks']}")
    print(f"  ✓ Available: {stats['available_checks']}")
    print(f"  ✗ Unavailable: {stats['unavailable_checks']}")
    print(f"  ⚠ Errors: {stats['error_checks']}")
    print(f"\nUptime: {stats['uptime_percentage']}%")

    if stats['avg_response_time_ms']:
        print(f"Avg response time: {stats['avg_response_time_ms']} ms")

    print("=" * 50)


if __name__ == "__main__":
    main()
