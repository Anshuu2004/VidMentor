import importlib
import time
from unittest.mock import MagicMock, patch
import httpx
import pytest

from groq import (
    APITimeoutError,
    RateLimitError,
    BadRequestError,
    AuthenticationError,
    APIConnectionError,
    InternalServerError,
)
import config
import llm


def make_timeout_error():
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    return APITimeoutError(request=req)


def make_rate_limit_error():
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(429, request=req)
    return RateLimitError("Rate limit reached", response=resp, body=None)


def make_bad_request_error():
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(400, request=req)
    return BadRequestError("Invalid model parameter", response=resp, body=None)


def make_auth_error():
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(401, request=req)
    return AuthenticationError("Invalid API key", response=resp, body=None)


def make_mock_completion(content="Test answer"):
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_resp.choices = [mock_choice]
    return mock_resp


# 1. Configured timeout is passed to Groq client
def test_configured_timeout_and_zero_sdk_retries_passed_to_client():
    assert llm.groq_client.timeout == config.GROQ_TIMEOUT_SEC
    assert llm.groq_client.max_retries == 0


def test_groq_client_init_uses_config_timeout(monkeypatch):
    orig_timeout = config.GROQ_TIMEOUT_SEC
    try:
        with patch("groq.Groq") as mock_groq_class:
            monkeypatch.setattr(config, "GROQ_TIMEOUT_SEC", 45.0)
            importlib.reload(llm)
            mock_groq_class.assert_called_with(
                api_key=config.GROQ_API_KEY,
                timeout=45.0,
                max_retries=0,
            )
    finally:
        monkeypatch.setattr(config, "GROQ_TIMEOUT_SEC", orig_timeout)
        importlib.reload(llm)

    assert llm.groq_client.timeout == orig_timeout


# 2. Transient timeout is retried within attempt limit
def test_transient_timeout_is_retried_within_attempt_limit(monkeypatch):
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    mock_create = MagicMock(
        side_effect=[
            make_timeout_error(),
            make_mock_completion("Answer on retry"),
        ]
    )
    monkeypatch.setattr(llm.groq_client.chat.completions, "create", mock_create)

    result = llm.call_groq_with_retry("test prompt", max_retries=3)

    assert result == "Answer on retry"
    assert mock_create.call_count == 2
    assert mock_sleep.call_count == 1
    assert mock_sleep.call_args[0][0] == 1.0  # 2 ** 0


# 3. Later successful attempt returns expected answer
def test_later_successful_attempt_returns_expected_answer(monkeypatch):
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    mock_create = MagicMock(
        side_effect=[
            make_timeout_error(),
            make_timeout_error(),
            make_mock_completion("Final success"),
        ]
    )
    monkeypatch.setattr(llm.groq_client.chat.completions, "create", mock_create)

    result = llm.call_groq_with_retry("test prompt", max_retries=3)

    assert result == "Final success"
    assert mock_create.call_count == 3
    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0][0][0] == 1.0  # 2 ** 0
    assert mock_sleep.call_args_list[1][0][0] == 2.0  # 2 ** 1


# 4. Exhausted timeouts produce intended controlled failure
def test_exhausted_timeouts_produce_controlled_failure(monkeypatch):
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    mock_create = MagicMock(side_effect=make_timeout_error())
    monkeypatch.setattr(llm.groq_client.chat.completions, "create", mock_create)

    with pytest.raises(APITimeoutError):
        llm.call_groq_with_retry("test prompt", max_retries=3)

    assert mock_create.call_count == 3
    # Sleeps happen only between attempts (attempts 0 and 1), not after exhaustion
    assert mock_sleep.call_count == 2


# 5. Permanent errors follow chosen retry policy (fail immediately without retry)
def test_permanent_bad_request_fails_immediately_without_retrying(monkeypatch):
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    mock_create = MagicMock(side_effect=make_bad_request_error())
    monkeypatch.setattr(llm.groq_client.chat.completions, "create", mock_create)

    with pytest.raises(BadRequestError):
        llm.call_groq_with_retry("test prompt", max_retries=3)

    assert mock_create.call_count == 1
    assert mock_sleep.call_count == 0


def test_permanent_auth_error_fails_immediately_without_retrying(monkeypatch):
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    mock_create = MagicMock(side_effect=make_auth_error())
    monkeypatch.setattr(llm.groq_client.chat.completions, "create", mock_create)

    with pytest.raises(AuthenticationError):
        llm.call_groq_with_retry("test prompt", max_retries=3)

    assert mock_create.call_count == 1
    assert mock_sleep.call_count == 0


def test_unrelated_errors_with_keywords_are_not_retried(monkeypatch):
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    # An unrelated exception containing words like 'timeout' or '429'
    mock_create = MagicMock(side_effect=RuntimeError("database timeout 429 error"))
    monkeypatch.setattr(llm.groq_client.chat.completions, "create", mock_create)

    with pytest.raises(RuntimeError):
        llm.call_groq_with_retry("test prompt", max_retries=3)

    # Must fail immediately on the first attempt without retrying
    assert mock_create.call_count == 1
    assert mock_sleep.call_count == 0


def test_is_transient_error_uses_only_sdk_classes():
    assert llm._is_transient_error(make_timeout_error()) is True
    assert llm._is_transient_error(make_rate_limit_error()) is True
    assert llm._is_transient_error(APIConnectionError(request=httpx.Request("POST", "https://api.groq.com"))) is True
    assert llm._is_transient_error(InternalServerError("Server error", response=httpx.Response(500, request=httpx.Request("POST", "https://api.groq.com")), body=None)) is True
    assert llm._is_transient_error(make_bad_request_error()) is False
    assert llm._is_transient_error(make_auth_error()) is False
    assert llm._is_transient_error(RuntimeError("429 rate limit timeout")) is False
    assert llm._is_transient_error(ValueError("timeout")) is False


# 6. Existing rate-limit retry behavior remains appropriate
def test_rate_limit_retry_recovers_on_next_attempt(monkeypatch):
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    mock_create = MagicMock(
        side_effect=[
            make_rate_limit_error(),
            make_mock_completion("Rate limit recovered"),
        ]
    )
    monkeypatch.setattr(llm.groq_client.chat.completions, "create", mock_create)

    result = llm.call_groq_with_retry("test prompt", max_retries=3)

    assert result == "Rate limit recovered"
    assert mock_create.call_count == 2
    assert mock_sleep.call_count == 1
    assert mock_sleep.call_args[0][0] == 1.0


def test_rate_limit_exhaustion_raises_controlled_exception(monkeypatch):
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    mock_create = MagicMock(side_effect=make_rate_limit_error())
    monkeypatch.setattr(llm.groq_client.chat.completions, "create", mock_create)

    with pytest.raises(RateLimitError):
        llm.call_groq_with_retry("test prompt", max_retries=3)

    assert mock_create.call_count == 3
    assert mock_sleep.call_count == 2


# 7. Retry sleeps are mocked and no real delays occur
def test_retry_sleeps_are_mocked_and_no_real_delays_occur(monkeypatch):
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    mock_create = MagicMock(
        side_effect=[
            make_timeout_error(),
            make_timeout_error(),
            make_mock_completion("Instant response"),
        ]
    )
    monkeypatch.setattr(llm.groq_client.chat.completions, "create", mock_create)

    result = llm.call_groq_with_retry("test prompt", max_retries=3)

    assert result == "Instant response"
    # Verify that sleep is intercepted by the mock with expected exponential delays
    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0][0][0] == 1.0
    assert mock_sleep.call_args_list[1][0][0] == 2.0


def test_retry_delay_is_bounded_by_max_delay(monkeypatch):
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    # Simulate 5 attempts (4 retries)
    mock_create = MagicMock(
        side_effect=[
            make_timeout_error(),
            make_timeout_error(),
            make_timeout_error(),
            make_timeout_error(),
            make_mock_completion("Eventual success"),
        ]
    )
    monkeypatch.setattr(llm.groq_client.chat.completions, "create", mock_create)

    result = llm.call_groq_with_retry("test prompt", max_retries=5)
    assert result == "Eventual success"
    # attempt 0: min(2^0, 8.0) = 1.0
    # attempt 1: min(2^1, 8.0) = 2.0
    # attempt 2: min(2^2, 8.0) = 4.0
    # attempt 3: min(2^3, 8.0) = 8.0 (capped at MAX_RETRY_DELAY_SEC)
    assert mock_sleep.call_args_list[0][0][0] == 1.0
    assert mock_sleep.call_args_list[1][0][0] == 2.0
    assert mock_sleep.call_args_list[2][0][0] == 4.0
    assert mock_sleep.call_args_list[3][0][0] == 8.0
