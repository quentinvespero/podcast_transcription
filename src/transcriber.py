import os
from pathlib import Path

import mlx_whisper

from src.config import TRANSCRIPTION_MODEL


def _is_hf_model_cached(hf_repo: str) -> bool:
    """Return True if the HuggingFace model weights are already in the local cache."""
    cache_dir = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
    cache_name = "models--" + hf_repo.replace("/", "--")
    return (cache_dir / cache_name).exists()


def transcribe(
    audio_path: str,
    model: str = TRANSCRIPTION_MODEL,
    language: str | None = None,
) -> list[dict]:
    """
    Transcribe an audio file using mlx-whisper (Apple Silicon optimised).

    Args:
        audio_path: Path to the .mp3 / .wav file.
        model:      HuggingFace repo for the MLX Whisper weights.
        language:   ISO 639-1 language code (e.g. "fr", "en").
                    Pass None to let Whisper auto-detect.

    Returns:
        List of segment dicts, each with:
          - start (float): start time in seconds
          - end   (float): end time in seconds
          - text  (str):   transcribed text for that segment
    """
    if _is_hf_model_cached(model):
        print(f"      Loading model {model} …")
    else:
        print(f"      Downloading model {model} (first run — this may take a few minutes) …")

    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hf_repo=model,
        language=language,
        # verbose=True prints each segment as it is decoded — useful progress indicator
        verbose=True,
        # word_timestamps adds overhead and we don't need them
        word_timestamps=False,
    )

    return [
        {
            "start": segment["start"],
            "end":   segment["end"],
            "text":  segment["text"].strip(),
        }
        for segment in result["segments"]
        # Drop empty segments that Whisper sometimes emits
        if segment["text"].strip()
    ]
