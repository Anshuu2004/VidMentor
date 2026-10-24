from config import PROMPT_HISTORY_MESSAGES
from prompts import build_prompt, format_context, format_history


def test_timestamp_is_minutes_and_zero_padded_seconds():
    chunks = [{"text": "hello", "start": 65, "end": 100}]
    assert format_context(chunks) == "[1:05] hello"


def test_empty_history_uses_placeholder():
    assert format_history([]) == "(no previous messages)"


def test_history_keeps_only_the_most_recent_messages():
    history = [{"role": "user", "content": f"m<{i}>"} for i in range(PROMPT_HISTORY_MESSAGES + 4)]
    text = format_history(history)
    assert "m<0>" not in text
    assert f"m<{PROMPT_HISTORY_MESSAGES + 3}>" in text


def test_prompt_contains_context_and_question():
    chunks = [{"text": "a hashmap gives O(1) lookup", "start": 10, "end": 50}]
    prompt = build_prompt(chunks, [], "why a hashmap?")
    assert "a hashmap gives O(1) lookup" in prompt
    assert "why a hashmap?" in prompt
    assert "Use ONLY the transcript context" in prompt