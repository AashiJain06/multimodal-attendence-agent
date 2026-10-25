from __future__ import annotations

import io
import numpy as np
import pandas as pd


def audio_features_available() -> bool:
    try:
        import soundfile  # noqa: F401
        return True
    except ImportError:
        return False


def analyze_audio(payload: bytes, filename: str, window_seconds: int = 5, noise_threshold: float = .22) -> pd.DataFrame:
    try:
        import soundfile as sf
        audio, sr = sf.read(io.BytesIO(payload), dtype="float32")
    except Exception as exc:
        raise ValueError("Could not decode audio. Use a PCM WAV file or install FFmpeg-compatible decoding.") from exc
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if len(audio) == 0 or sr <= 0:
        raise ValueError("Audio contains no usable samples.")
    window = max(1, int(window_seconds * sr))
    rows = []
    for start in range(0, len(audio), window):
        segment = audio[start:start+window]
        if len(segment) == 0:
            continue
        rms = float(np.sqrt(np.mean(segment ** 2) + 1e-12))
        # Short-time energy proxy, zero-crossing rate and simple energy gate.
        zcr = float(np.mean(np.abs(np.diff(np.signbit(segment))))) if len(segment) > 1 else 0.0
        speech_ratio = float(np.mean(np.abs(segment) > max(.008, rms * .35)))
        if rms < .012:
            label = "Silence"
        elif rms >= noise_threshold:
            label = "High Ambient Classroom Distraction"
        elif speech_ratio > .32 and zcr < .22:
            label = "Student Discussion / Verbal Interaction" if zcr > .045 else "Instructor Lecture"
        else:
            label = "High Ambient Classroom Distraction"
        rows.append({
            "time_seconds": round(start / sr, 2),
            "time_label": f"{int(start/sr)//60:02d}:{int(start/sr)%60:02d}",
            "duration_seconds": round(len(segment)/sr, 2),
            "rms_energy": round(rms, 4),
            "zero_crossing_rate": round(zcr, 4),
            "speech_ratio": round(speech_ratio, 3),
            "class": label,
        })
    return pd.DataFrame(rows)
