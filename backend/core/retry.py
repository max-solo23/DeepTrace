"""
Retry Logic Module

Implements exponential backoff retry strategy for resilient agent operations.
Follows Error Handling Policy: retry → fallback → degrade gracefully.
"""

import asyncio
import logging
from typing import TypeVar, Callable, Any, Optional
from functools import wraps


# Configure logger
logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_with_backoff(
    func: Callable[..., Any],
    *args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    **kwargs
) -> Optional[Any]:
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        *args: Positional arguments to pass to func
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries (default: 10.0)
        exponential_base: Multiplier for exponential backoff (default: 2.0)
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from func if successful, None if all attempts fail

    Example:
        result = await retry_with_backoff(
            some_async_function,
            arg1, arg2,
            max_attempts=3,
            base_delay=1.0
        )

    Logs:
        - Each retry attempt with attempt number
        - Final failure if all attempts exhausted
    """
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(
                f"Attempt {attempt}/{max_attempts} for {func.__name__}"
            )
            result = await func(*args, **kwargs)

            if attempt > 1:
                logger.info(
                    f"{func.__name__} succeeded on attempt {attempt}"
                )

            return result

        except Exception as exc:
            last_exception = exc
            logger.warning(
                f"{func.__name__} failed on attempt {attempt}/{max_attempts}: "
                f"{type(exc).__name__}: {str(exc)}"
            )

            # Don't sleep after the last attempt
            if attempt < max_attempts:
                # Calculate delay with exponential backoff
                delay = min(
                    base_delay * (exponential_base ** (attempt - 1)),
                    max_delay
                )
                logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)

    # All attempts failed
    logger.error(
        f"{func.__name__} failed after {max_attempts} attempts. "
        f"Last error: {type(last_exception).__name__}: {str(last_exception)}"
    )
    return None


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0
):
    """
    Decorator for adding retry logic to async functions.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries (default: 10.0)
        exponential_base: Multiplier for exponential backoff (default: 2.0)

    Example:
        @with_retry(max_attempts=3, base_delay=1.0)
        async def fetch_data(url: str):
            # ... implementation
            pass

    Returns:
        Decorated function that retries on failure
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(
                func,
                *args,
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                **kwargs
            )
        return wrapper
    return decorator


async def retry_with_fallback(
    primary_func: Callable[..., Any],
    fallback_func: Callable[..., Any],
    *args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    **kwargs
) -> Optional[Any]:
    """
    Try primary function with retries, fallback to alternative if all fail.

    Args:
        primary_func: Primary async function to try
        fallback_func: Fallback async function if primary fails
        *args: Arguments to pass to both functions
        max_attempts: Maximum retry attempts for primary (default: 3)
        base_delay: Initial delay for retries (default: 1.0)
        **kwargs: Keyword arguments to pass to both functions

    Returns:
        Result from primary_func if successful, otherwise from fallback_func

    Example:
        result = await retry_with_fallback(
            fetch_from_api,
            fetch_from_cache,
            query="example",
            max_attempts=3
        )
    """
    logger.info(f"Trying primary function: {primary_func.__name__}")

    # Try primary function with retries
    result = await retry_with_backoff(
        primary_func,
        *args,
        max_attempts=max_attempts,
        base_delay=base_delay,
        **kwargs
    )

    if result is not None:
        return result

    # Primary failed, try fallback
    logger.info(
        f"Primary function {primary_func.__name__} failed. "
        f"Attempting fallback: {fallback_func.__name__}"
    )

    try:
        fallback_result = await fallback_func(*args, **kwargs)
        logger.info(f"Fallback {fallback_func.__name__} succeeded")
        return fallback_result
    except Exception as exc:
        logger.error(
            f"Fallback {fallback_func.__name__} also failed: "
            f"{type(exc).__name__}: {str(exc)}"
        )
        return None


# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
