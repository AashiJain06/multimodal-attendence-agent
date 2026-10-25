from __future__ import annotations

import numpy as np
import pandas as pd


def build_engagement_matrix(audio: pd.DataFrame, visual_attention: int, interaction: int, posture: int) -> pd.DataFrame:
    visual = float(np.clip(visual_attention, 0, 100))
    posture = float(np.clip(posture, 0, 100))
    interaction = float(np.clip(interaction, 0, 100))
    if audio is not None and not audio.empty:
        rows = []
        for _, r in audio.iterrows():
            acoustic = min(100.0, max(0.0, float(r.get("speech_ratio", 0)) * 100))
            # A loud-noise label is not treated as positive engagement.
            label = str(r.get("class", ""))
            interaction_signal = acoustic if "Discussion" in label else interaction
            score = .45 * visual + .20 * posture + .35 * interaction_signal
            if "High Ambient" in label:
                score *= .72
            rows.append({
                "time_seconds": float(r.get("time_seconds", 0)),
                "time_label": str(r.get("time_label", "")),
                "visual_attention": round(visual, 1),
                "upright_posture": round(posture, 1),
                "interaction_energy": round(interaction_signal, 1),
                "acoustic_class": label,
                "engagement_index": round(float(np.clip(score, 0, 100)), 1),
            })
        return pd.DataFrame(rows)
    score = .45 * visual + .20 * posture + .35 * interaction
    return pd.DataFrame([{
        "time_seconds": 0,
        "time_label": "00:00",
        "visual_attention": visual,
        "upright_posture": posture,
        "interaction_energy": interaction,
        "acoustic_class": "Manual estimate",
        "engagement_index": round(float(np.clip(score, 0, 100)), 1),
    }])


def engagement_score(df: pd.DataFrame) -> float:
    if df is None or df.empty:
        return 0.0
    return float(np.clip(df["engagement_index"].mean(), 0, 100))
