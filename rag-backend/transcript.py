
import logging

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
from config import PREFERRED_LANGS

logger = logging.getLogger(__name__)


def get_transcript(video_id, preferred_langs=PREFERRED_LANGS):
    ytt_api = YouTubeTranscriptApi()

    try:
        fetched = ytt_api.fetch(
            video_id,
            languages=list(preferred_langs),
        )
        return fetched.to_raw_data(), None

    except NoTranscriptFound:
        try:
            transcript_list = ytt_api.list(video_id)
            first_available = next(iter(transcript_list))
            return first_available.fetch().to_raw_data(), None

        except StopIteration:
            return None, "No transcript available in any language for this video."

        except Exception:
            logger.exception(
                "Error while looking for an available transcript for video %s",
                video_id,
            )
            return None, "No transcript available in any language for this video."

    except TranscriptsDisabled:
        return None, "Captions are disabled for this video."

    except VideoUnavailable:
        return None, "Video not found or unavailable."

    except Exception:
        logger.exception(
            "Unexpected error while fetching transcript for video %s",
            video_id,
        )
        return (
            None,
            "Sorry, we couldn't fetch the transcript right now. Please try again later.",
        )
