import logging
import requests
from fastapi import HTTPException
from vibe2025.cache import forex_cache

logger = logging.getLogger(__name__)


async def get_exchange_rate(source: str, target: str, use_cache: bool = True) -> float:
    """
    Fetch current exchange rate from open.er-api.com with caching.

    Args:
        source: Source currency code (e.g., 'EUR')
        target: Target currency code (e.g., 'USD')
        use_cache: Whether to use cached rates (default: True)

    Returns:
        Exchange rate as float

    Raises:
        HTTPException: If API request fails or currency not found
    """
    # Check cache first
    if use_cache:
        cached_rate = forex_cache.get(source, target)
        if cached_rate is not None:
            logger.info(f"Using cached rate: {source}/{target} = {cached_rate}")
            return cached_rate

    # Fetch from API
    url = f"https://open.er-api.com/v6/latest/{source}"
    logger.debug(f"Fetching exchange rate from: {url}")

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        logger.debug(f"API response status: {data.get('result')}")

        if data.get("result") == "success":
            rates = data.get("rates", {})
            if target not in rates:
                logger.warning(f"Currency {target} not found in rates")
                raise HTTPException(
                    status_code=404,
                    detail=f"Currency {target} not found"
                )

            rate = rates[target]
            logger.info(f"Successfully fetched rate: {source}/{target} = {rate}")

            # Cache the result
            if use_cache:
                forex_cache.set(source, target, rate)

            return rate
        else:
            logger.error(f"API returned unsuccessful result: {data.get('result')}")
            raise HTTPException(
                status_code=503,
                detail="Exchange rate service unavailable"
            )
    except requests.Timeout:
        logger.error(f"Timeout fetching exchange rate for {source}/{target}")
        raise HTTPException(
            status_code=503,
            detail="Exchange rate service timeout"
        )
    except requests.RequestException as e:
        logger.error(f"Request failed for {source}/{target}: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch exchange rates: {str(e)}"
        )
