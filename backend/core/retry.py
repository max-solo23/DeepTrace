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


# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
