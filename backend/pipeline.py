"""
Pipeline that runs: (optional STT) -> summarise -> translate -> TTS.

The UI calls run_pipeline() with either text or an uploaded audio file.
We yield progress updates so Streamlit can show what's happening.
"""

import io
from mutagen import File as MutagenFile

from backend.sunbird_client import stt, summarise, translate, tts

MAX_AUDIO_SECONDS = 5 * 60  # 5 minutes


class PipelineError(Exception):
    """Raised when the pipeline cannot continue."""
    pass


def check_audio_duration(audio_bytes: bytes, filename: str) -> float:
    """
    Read audio metadata and return duration in seconds.
    Raises PipelineError if the file is unreadable or longer than 5 minutes.
    """
    try:
        # mutagen needs a file-like object with a name
        buf = io.BytesIO(audio_bytes)
        buf.name = filename
        meta = MutagenFile(buf)
    except Exception as e:
        raise PipelineError(f"Could not read audio file: {e}")

    if meta is None or not getattr(meta, "info", None):
        raise PipelineError(
            "Could not read audio metadata. Please use MP3, WAV, OGG, M4A, or AAC."
        )

    duration = meta.info.length
    if duration > MAX_AUDIO_SECONDS:
        mins = duration / 60
        raise PipelineError(
            f"Audio is {mins:.1f} minutes long. The limit is 5 minutes."
        )
    return duration


def run_pipeline(
    *,
    text_input: str = None,
    audio_bytes: bytes = None,
    audio_filename: str = None,
    target_language: str = "Luganda",
):
    """
    Run the full pipeline.

    Provide EITHER text_input OR (audio_bytes + audio_filename), not both.
    Returns a dict with keys: original_text, summary, translation, audio_bytes.

    This is a generator: it yields ("status", message) tuples so the UI
    can show progress, then finally yields ("result", result_dict).
    """
    if not text_input and not audio_bytes:
        raise PipelineError("Please provide either text or an audio file.")
    if text_input and audio_bytes:
        raise PipelineError("Provide either text or audio, not both.")

    # Step 1: get the source text
    if audio_bytes:
        yield ("status", "Checking audio length...")
        check_audio_duration(audio_bytes, audio_filename or "audio.mp3")

        yield ("status", "Transcribing audio...")
        original_text = stt(audio_bytes, audio_filename or "audio.mp3")
    else:
        original_text = text_input.strip()
        if not original_text:
            raise PipelineError("Text input is empty.")

    # Step 2: summarise
    yield ("status", "Summarising...")
    summary = summarise(original_text)

    # Step 3: translate
    yield ("status", f"Translating to {target_language}...")
    translation = translate(summary, target_language)

    # Step 4: synthesise speech
    yield ("status", "Generating audio...")
    audio_out = tts(translation, target_language)

    yield ("result", {
        "original_text": original_text,
        "summary": summary,
        "translation": translation,
        "audio_bytes": audio_out,
        "target_language": target_language,
    })
