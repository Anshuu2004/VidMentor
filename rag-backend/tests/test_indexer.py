import indexer


def test_empty_transcript_returns_friendly_error(monkeypatch):
    monkeypatch.setattr(indexer, "get_transcript", lambda video_id: ([], None))
    result, error = indexer.build_index_for_video("abc123")
    assert result is None
    assert error