
import logging

import pytest
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

import transcript


class FakeFetchedTranscript:
    def to_raw_data(self):
        return [{"text": "Hello world", "start": 0.0, "duration": 2.0}]


class FakeAvailableTranscript:
    def fetch(self):
        return FakeFetchedTranscript()


class FakeTranscriptAPI:
    def __init__(self, fetch_result=None, fetch_error=None, transcripts=None):
        self.fetch_result = fetch_result or FakeFetchedTranscript()
        self.fetch_error = fetch_error
        self.transcripts = transcripts if transcripts is not None else []

    def fetch(self, video_id, languages):
        if self.fetch_error:
            raise self.fetch_error
        return self.fetch_result

    def list(self, video_id):
        return iter(self.transcripts)


def test_get_transcript_success(monkeypatch):
    monkeypatch.setattr(
        transcript,
        "YouTubeTranscriptApi",
        lambda: FakeTranscriptAPI(),
    )

    data, error = transcript.get_transcript("video123")

    assert data == [{"text": "Hello world", "start": 0.0, "duration": 2.0}]
    assert error is None


def test_empty_transcript_list_does_not_log_error(monkeypatch, caplog):
    class EmptyTranscriptAPI(FakeTranscriptAPI):
        def fetch(self, video_id, languages):
            raise NoTranscriptFound(video_id, languages, None)

    monkeypatch.setattr(
        transcript,
        "YouTubeTranscriptApi",
        lambda: EmptyTranscriptAPI(),
    )

    with caplog.at_level(logging.ERROR):
        data, error = transcript.get_transcript("video123")

    assert data is None
    assert error == "No transcript available in any language for this video."
    assert not caplog.records


def test_unexpected_fetch_error_is_logged(monkeypatch, caplog):
    monkeypatch.setattr(
        transcript,
        "YouTubeTranscriptApi",
        lambda: FakeTranscriptAPI(fetch_error=RuntimeError("network failure")),
    )

    with caplog.at_level(logging.ERROR):
        data, error = transcript.get_transcript("video123")

    assert data is None
    assert error == (
        "Sorry, we couldn't fetch the transcript right now. Please try again later."
    )
    assert "Unexpected error while fetching transcript" in caplog.text
    assert "network failure" in caplog.text


def test_transcripts_disabled(monkeypatch):
    monkeypatch.setattr(
        transcript,
        "YouTubeTranscriptApi",
        lambda: FakeTranscriptAPI(fetch_error=TranscriptsDisabled("video123")),
    )

    data, error = transcript.get_transcript("video123")

    assert data is None
    assert error == "Captions are disabled for this video."


def test_video_unavailable(monkeypatch):
    monkeypatch.setattr(
        transcript,
        "YouTubeTranscriptApi",
        lambda: FakeTranscriptAPI(fetch_error=VideoUnavailable("video123")),
    )

    data, error = transcript.get_transcript("video123")

    assert data is None
    assert error == "Video not found or unavailable."


def test_fallback_transcript_is_used(monkeypatch):
    class FallbackAPI(FakeTranscriptAPI):
        def fetch(self, video_id, languages):
            raise NoTranscriptFound(video_id, languages, None)

        def list(self, video_id):
            return iter([FakeAvailableTranscript()])

    monkeypatch.setattr(
        transcript,
        "YouTubeTranscriptApi",
        lambda: FallbackAPI(),
    )

    data, error = transcript.get_transcript("video123")

    assert data == [{"text": "Hello world", "start": 0.0, "duration": 2.0}]
    assert error is None
