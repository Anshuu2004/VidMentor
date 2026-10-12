from chunking import chunk_transcript


def seg(text, start):
    return {"text": text, "start": start, "duration": 2.0}


def test_short_transcript_makes_one_chunk():
    chunks = chunk_transcript([seg("a", 0), seg("b", 10), seg("c", 20)], window_sec=40)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "a b c"
    assert chunks[0]["start"] == 0


def test_splits_when_window_is_exceeded():
    t = [seg("a", 0), seg("b", 30), seg("c", 41), seg("d", 50)]
    chunks = chunk_transcript(t, window_sec=40)
    assert [c["text"] for c in chunks] == ["a b", "c d"]


def test_segment_exactly_at_boundary_stays_in_chunk():
    assert len(chunk_transcript([seg("a", 0), seg("b", 40)], window_sec=40)) == 1


def test_no_text_is_lost_across_chunks():
    t = [seg(str(i), i * 7) for i in range(50)]
    chunks = chunk_transcript(t, window_sec=40)
    assert " ".join(c["text"] for c in chunks).split() == [str(i) for i in range(50)]


def test_chunk_start_is_not_after_end():
    t = [seg(str(i), i * 7) for i in range(50)]
    for c in chunk_transcript(t, window_sec=40):
        assert c["start"] <= c["end"]


def test_empty_transcript_returns_no_chunks():
    assert chunk_transcript([]) == []