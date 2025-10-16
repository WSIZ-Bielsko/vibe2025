import asyncio
import socket
import time
from datetime import datetime
from vibe2025.uptime_checker.models import CheckResult


async def check_service_availability(
        host: str,
        port: int,
        timeout: float
) -> CheckResult:
    """
    Check if a service is available by attempting to connect.

    Args:
        host: IP address or domain name
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        CheckResult with availability status
    """
    start_time = time.perf_counter()

    try:
        # Use asyncio.wait_for to enforce timeout
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )

        # Connection successful
        writer.close()
        await writer.wait_closed()

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return CheckResult(
            host=host,
            port=port,
            status="available",
            timestamp=datetime.now(),
            response_time_ms=round(elapsed_ms, 2)
        )

    except asyncio.TimeoutError:
        return CheckResult(
            host=host,
            port=port,
            status="unavailable",
            timestamp=datetime.now(),
            error_message=f"Connection timeout after {timeout}s"
        )

    except (socket.gaierror, OSError, ConnectionRefusedError) as e:
        return CheckResult(
            host=host,
            port=port,
            status="error",
            timestamp=datetime.now(),
            error_message=str(e)
        )


async def check_all_services(
        services: list[tuple[str, int]],
        timeout: float
) -> list[CheckResult]:
    """
    Check availability of all services concurrently.

    Args:
        services: List of (host, port) tuples
        timeout: Connection timeout in seconds

    Returns:
        List of CheckResult objects
    """
    tasks = [
        check_service_availability(host, port, timeout)
        for host, port in services
    ]

    return await asyncio.gather(*tasks)
