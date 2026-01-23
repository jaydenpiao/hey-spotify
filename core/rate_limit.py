"""Rate limiting and backoff utilities."""
import asyncio
import random
from typing import Callable, TypeVar, Any
from functools import wraps

from core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff delay with jitter.
    
    Args:
        attempt: Attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    # Add jitter (±25%)
    jitter = delay * 0.25 * (random.random() * 2 - 1)
    return max(0, delay + jitter)


async def retry_with_backoff(
    func: Callable[..., Any],
    max_retries: int = 3,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    backoff_base: float = 1.0,
) -> Any:
    """Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        retry_on: Tuple of exception types to retry on
        backoff_base: Base delay for exponential backoff
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except retry_on as e:
            last_exception = e
            
            if attempt < max_retries:
                delay = calculate_backoff(attempt, base_delay=backoff_base)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. Retrying in {delay:.2f}s...",
                    extra={"attempt": attempt + 1, "delay_seconds": delay}
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {max_retries + 1} attempts failed",
                    extra={"attempts": max_retries + 1}
                )
    
    raise last_exception
