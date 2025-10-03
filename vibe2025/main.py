import logging
from fastapi import FastAPI, HTTPException, Query
from vibe2025.forex import get_exchange_rate
from vibe2025.models import ConversionResponse
from vibe2025.cache import forex_cache
from decimal import Decimal, getcontext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vibe2025.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Currency Converter API",
    description="Real-time forex currency conversion with caching",
    version="0.1.0"
)


@app.on_event("startup")
async def startup_event():
    logger.info("Currency Converter API starting up")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Currency Converter API shutting down")


@app.get("/convert", response_model=ConversionResponse)
async def convert_currency(
        pair: str = Query(..., min_length=6, max_length=6, description="Currency pair (e.g., EURUSD)"),
        volume: float = Query(..., gt=0, description="Amount to convert"),
        no_cache: bool = Query(False, description="Skip cache and fetch fresh rate")
):
    """Convert currency using live forex rates."""
    logger.info(f"Conversion request: pair={pair}, volume={volume}, no_cache={no_cache}")

    source = pair[:3].upper()
    target = pair[3:].upper()

    try:
        rate = await get_exchange_rate(source, target, use_cache=not no_cache)
        logger.debug(f"Exchange rate fetched: {source}/{target} = {rate}")

        getcontext().prec = 10
        result = float(Decimal(str(rate)) * Decimal(str(volume)))

        logger.info(f"Conversion successful: {volume} {source} = {result} {target}")
        return ConversionResponse(result=result)
    except HTTPException as e:
        logger.error(f"Conversion failed: {e.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during conversion: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    stats = forex_cache.get_stats()
    logger.debug(f"Cache stats requested: {stats}")
    return stats


@app.post("/cache/clear")
async def clear_cache():
    """Clear all cached rates."""
    forex_cache.clear()
    logger.info("Cache cleared via API")
    return {"message": "Cache cleared successfully"}


@app.get("/")
async def root():
    logger.debug("Root endpoint accessed")
    return {"message": "Currency Converter API", "docs": "/docs"}
