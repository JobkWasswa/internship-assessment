"""
Sunbird AI — Speak & Translate
Streamlit app that takes text or audio, summarises, translates to a Ugandan
language, and reads the translation aloud.
"""

import streamlit as st
from dotenv import load_dotenv

from backend.pipeline import run_pipeline, PipelineError
from backend.sunbird_client import SUPPORTED_LANGUAGES, SunbirdAPIError

load_dotenv()

st.set_page_config(
    page_title="Sunbird AI — Speak & Translate",
    page_icon="🌻",
    layout="centered",
)

st.title("🌻 Speak & Translate")
st.caption(
    "Powered by Sunbird AI. Give it text or audio, get a summary translated "
    "into a Ugandan local language — with a spoken audio version."
)

# --- Inputs ---
with st.container(border=True):
    st.subheader("1. Choose your input")

    input_mode = st.radio(
        "Input type",
        options=["Text", "Audio"],
        horizontal=True,
        label_visibility="collapsed",
    )

    text_value = None
    audio_file = None

    if input_mode == "Text":
        text_value = st.text_area(
            "Type or paste text",
            height=180,
            placeholder="Paste an article, a story, or any passage in English...",
        )
    else:
        audio_file = st.file_uploader(
            "Upload an audio file (max 5 minutes)",
            type=["mp3", "wav", "ogg", "m4a", "aac"],
        )
        if audio_file is not None:
            st.audio(audio_file)

with st.container(border=True):
    st.subheader("2. Choose a target language")
    target_language = st.selectbox(
        "Translate the summary into",
        SUPPORTED_LANGUAGES,
        index=0,
        label_visibility="collapsed",
    )

run_clicked = st.button("Run pipeline", type="primary", use_container_width=True)

# --- Pipeline execution ---
if run_clicked:
    # Build the kwargs for run_pipeline based on which input the user chose
    kwargs = {"target_language": target_language}
    if input_mode == "Text":
        if not text_value or not text_value.strip():
            st.error("Please type some text first.")
            st.stop()
        kwargs["text_input"] = text_value
    else:
        if audio_file is None:
            st.error("Please upload an audio file first.")
            st.stop()
        kwargs["audio_bytes"] = audio_file.getvalue()
        kwargs["audio_filename"] = audio_file.name

    status = st.status("Starting...", expanded=True)
    result = None

    try:
        for kind, payload in run_pipeline(**kwargs):
            if kind == "status":
                status.update(label=payload)
                status.write(payload)
            elif kind == "result":
                result = payload
        status.update(label="Done", state="complete")
    except PipelineError as e:
        status.update(label="Pipeline error", state="error")
        st.error(str(e))
    except SunbirdAPIError as e:
        status.update(label="Sunbird API error", state="error")
        st.error(str(e))
    except Exception as e:
        status.update(label="Unexpected error", state="error")
        st.error(f"Something went wrong: {e}")

    # --- Outputs ---
    if result is not None:
        st.success("Pipeline finished.")

        st.subheader("Original text")
        st.write(result["original_text"])

        st.subheader("Summary (English)")
        st.write(result["summary"])

        st.subheader(f"Translated summary ({result['target_language']})")
        st.write(result["translation"])

        st.subheader(f"Audio ({result['target_language']})")
        st.audio(result["audio_bytes"])
        st.download_button(
            "Download audio",
            data=result["audio_bytes"],
            file_name=f"summary_{result['target_language'].lower()}.wav",
            mime="audio/wav",
        )

# --- Footer ---
st.divider()
st.caption(
    "Languages supported: " + ", ".join(SUPPORTED_LANGUAGES) +
    " · Audio cap: 5 minutes · APIs: Sunbird AI STT, Sunflower LLM, Sunbird AI TTS"
)
