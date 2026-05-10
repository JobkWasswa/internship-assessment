"""
Thin wrapper around the Sunbird AI API.

One function per endpoint we use:
  - stt(audio_bytes, filename)  -> transcript text
  - summarise(text)             -> summary text
  - translate(text, language)   -> translated text
  - tts(text, language)         -> audio bytes (mp3/wav)

Each function raises SunbirdAPIError on failure with a readable message.
"""

import os
import requests

BASE_URL = "https://api.sunbird.ai"

# Speaker IDs from the TTS docs (one female voice per supported language)
SPEAKER_IDS = {
    "Luganda": 248,
    "Acholi": 241,
    "Ateso": 242,
    "Runyankole": 243,
    "Lugbara": 245,
}

SUPPORTED_LANGUAGES = list(SPEAKER_IDS.keys())


class SunbirdAPIError(Exception):
    """Raised when a Sunbird API call fails."""
    pass


def _get_token():
    token = os.getenv("SUNBIRD_API_TOKEN")
    if not token:
        raise SunbirdAPIError(
            "SUNBIRD_API_TOKEN is not set. Add it to your .env file or "
            "as a Hugging Face Space secret."
        )
    return token.strip()


def _auth_headers(json_body=False):
    headers = {"Authorization": f"Bearer {_get_token()}"}
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def _post(url, **kwargs):
    """POST helper with consistent error handling."""
    try:
        resp = requests.post(url, timeout=120, **kwargs)
    except requests.exceptions.RequestException as e:
        raise SunbirdAPIError(f"Network error calling {url}: {e}")

    if resp.status_code >= 400:
        # Try to surface the API's own error message if there is one
        try:
            detail = resp.json()
        except ValueError:
            detail = resp.text
        raise SunbirdAPIError(
            f"Sunbird API returned {resp.status_code}: {detail}"
        )
    return resp


def stt(audio_bytes: bytes, filename: str = "audio.mp3") -> str:
    """Transcribe an audio file. Returns the transcript text."""
    url = f"{BASE_URL}/tasks/modal/stt"

    # Pick a MIME type from the filename extension
    ext = (filename.rsplit(".", 1)[-1] or "").lower()
    mime_map = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        "mp4": "audio/mp4",
        "webm": "audio/webm",
    }
    mime = mime_map.get(ext, "application/octet-stream")

    # Pass (filename, bytes, mime) so requests sets Content-Type correctly
    files = {"audio": (filename, audio_bytes, mime)}
    headers = {"Authorization": f"Bearer {_get_token()}"}
    resp = _post(url, files=files, headers=headers)

    data = resp.json()
    text = (data.get("audio_transcription") or "").strip()
    if not text:
        raise SunbirdAPIError("STT returned an empty transcript.")
    return text


def _sunflower_simple(instruction: str) -> str:
    """Single-turn call to the Sunflower LLM. Uses form-encoded body."""
    url = f"{BASE_URL}/tasks/sunflower_simple"
    # The endpoint expects form data, not JSON
    form_data = {
        "instruction": instruction,
        "model_type": "qwen",
        "temperature": "0.3",
    }
    # Don't set Content-Type — requests sets it correctly for form data
    headers = {"Authorization": f"Bearer {_get_token()}"}
    resp = _post(url, data=form_data, headers=headers)

    data = resp.json()
    # The response field is "response" for this endpoint
    output = data.get("response", "")
    if isinstance(output, dict):
        output = output.get("content", "")
    output = (output or "").strip()
    if not output:
        raise SunbirdAPIError("Sunflower returned an empty response.")
    return output


def summarise(text: str) -> str:
    """Summarise a passage of text using Sunflower."""
    prompt = (
        "Summarise the following text in 3 to 5 clear sentences. "
        "Keep the main facts and tone, and do not add information that "
        "is not in the original.\n\n"
        f"Text:\n{text}\n\nSummary:"
    )
    return _sunflower_simple(prompt)


def translate(text: str, language: str) -> str:
    """Translate text into one of the supported Ugandan languages."""
    if language not in SUPPORTED_LANGUAGES:
        raise SunbirdAPIError(f"Unsupported language: {language}")

    prompt = (
        f"Translate the following English text into {language}. "
        f"Return only the {language} translation with no extra commentary.\n\n"
        f"English:\n{text}\n\n{language}:"
    )
    return _sunflower_simple(prompt)


def tts(text: str, language: str) -> bytes:
    """Generate speech from text in the chosen language. Returns audio bytes."""
    if language not in SPEAKER_IDS:
        raise SunbirdAPIError(f"No TTS voice available for {language}")

    url = f"{BASE_URL}/tasks/tts"
    payload = {"text": text, "speaker_id": SPEAKER_IDS[language]}
    resp = _post(url, json=payload, headers=_auth_headers(json_body=True))

    data = resp.json()
    audio_url = data.get("output", {}).get("audio_url")
    if not audio_url:
        raise SunbirdAPIError("TTS response did not include an audio URL.")

    # The audio URL is a short-lived signed URL — download it now.
    try:
        audio_resp = requests.get(audio_url, timeout=60)
        audio_resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SunbirdAPIError(f"Failed to download generated audio: {e}")

    return audio_resp.content
