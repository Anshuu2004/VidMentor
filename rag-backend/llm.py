import logging
import time
from groq import (
    Groq,
    APITimeoutError,
    RateLimitError,
    APIConnectionError,
    InternalServerError,
    APIStatusError,
    BadRequestError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    UnprocessableEntityError,
)
from config import GROQ_API_KEY, GROQ_TIMEOUT_SEC, LLM_MODEL, LLM_TEMPERATURE, MAX_RETRIES

logger = logging.getLogger(__name__)

# Initialize the Groq client.
# max_retries is deliberately set to 0 at the SDK level to avoid multiplying retries;
# bounded retries and exponential backoff are explicitly orchestrated by call_groq_with_retry.
groq_client = Groq(
    api_key=GROQ_API_KEY,
    timeout=GROQ_TIMEOUT_SEC,
    max_retries=0,
)

# Maximum delay between retry attempts in seconds to prevent unbounded backoff
MAX_RETRY_DELAY_SEC = 8.0


def _is_transient_error(exc: Exception) -> bool:
    """Determine whether an error is transient and should be retried."""
    if isinstance(exc, (APITimeoutError, RateLimitError, APIConnectionError, InternalServerError)):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code is not None and exc.status_code >= 500:
        return True
    # Permanent client errors (4xx except 429) must never be retried
    if isinstance(
        exc,
        (
            BadRequestError,
            AuthenticationError,
            PermissionDeniedError,
            NotFoundError,
            UnprocessableEntityError,
        ),
    ):
        return False
    if isinstance(exc, APIStatusError) and exc.status_code is not None and 400 <= exc.status_code < 500:
        return False
    # Fallback pattern matching for mock exceptions or custom subclasses
    err_str = str(exc).lower()
    if "429" in err_str or "rate limit" in err_str or "timeout" in err_str:
        return True
    return False


def call_groq_with_retry(prompt: str, max_retries: int = MAX_RETRIES) -> str:
    """Call the Groq API with bounded exponential backoff retries for transient failures.

    Args:
        prompt: The formatted prompt to send to the LLM.
        max_retries: Total number of attempts allowed (1 initial attempt + up to max_retries - 1 retries).
            Defaults to MAX_RETRIES from config (3 attempts).

    Returns:
        The generated answer text from the model.

    Raises:
        APITimeoutError: When request times out and retry attempts are exhausted.
        RateLimitError: When rate limit is encountered and retry attempts are exhausted.
        Exception: The underlying exception when retries are exhausted or a permanent error occurs.
    """
    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=LLM_TEMPERATURE,
            )
            return response.choices[0].message.content
        except Exception as e:
            if _is_transient_error(e) and attempt < max_retries - 1:
                delay = min(2 ** attempt, MAX_RETRY_DELAY_SEC)
                logger.warning(
                    "Groq API transient error on attempt %d/%d (%s). Retrying in %.1fs...",
                    attempt + 1,
                    max_retries,
                    type(e).__name__,
                    delay,
                )
                time.sleep(delay)
            else:
                if not _is_transient_error(e):
                    logger.error(
                        "Groq API non-retryable error on attempt %d/%d (%s): %s",
                        attempt + 1,
                        max_retries,
                        type(e).__name__,
                        e,
                    )
                else:
                    logger.error(
                        "Groq API retry attempts exhausted (%d/%d): %s",
                        max_retries,
                        max_retries,
                        e,
                    )
                raise
