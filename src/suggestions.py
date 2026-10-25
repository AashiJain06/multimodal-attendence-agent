from __future__ import annotations

import pandas as pd


def generate_suggestions(engagement: pd.DataFrame, audio: pd.DataFrame) -> list[dict]:
    suggestions = []
    if engagement is None or engagement.empty:
        return [{
            "title": "Start with a quick pulse check",
            "prompt": "Try a one-question poll or ask learners to summarize the key idea in pairs, then review the room's response.",
            "signal": "No engagement timeline available",
            "confidence": "Low — generic suggestion",
        }]
    mean_score = float(engagement["engagement_index"].mean())
    low = engagement[engagement["engagement_index"] < 45]
    if mean_score < 45:
        suggestions.append({
            "title": "Try an active-learning reset",
            "prompt": "Collective engagement estimates are low. Consider a one-question poll, think-pair-share, or a two-minute stretch break, then check understanding.",
            "signal": f"Mean collective index {mean_score:.0f}/100",
            "confidence": "Heuristic — educator judgment required",
        })
    if len(low) >= 2:
        duration = float(low["time_seconds"].max() - low["time_seconds"].min()) if "time_seconds" in low else 0
        if duration >= 240 or len(low) >= 5:
            suggestions.append({
                "title": "Break up the current activity",
                "prompt": "Several time windows are below the engagement threshold. Pause for a retrieval question, invite a student-generated example, or change modality for a few minutes.",
                "signal": f"{len(low)} low-index time windows",
                "confidence": "Heuristic — not an individual attention judgment",
            })
    if audio is not None and not audio.empty:
        noise = int((audio["class"] == "High Ambient Classroom Distraction").sum())
        if noise >= max(2, len(audio) // 3):
            suggestions.append({
                "title": "Check room acoustics and activity fit",
                "prompt": "Multiple windows have high ambient energy. Check whether this is expected group-work noise, equipment noise, or a need for clearer turn-taking cues.",
                "signal": f"{noise}/{len(audio)} windows labelled high ambient energy",
                "confidence": "Low to medium — energy labels are not semantic understanding",
            })
    if not suggestions:
        suggestions.append({
            "title": "Reinforce what is working",
            "prompt": "Collective signals are not showing a sustained dip. Continue the current format and use a short retrieval question to verify learning rather than relying on attention estimates.",
            "signal": f"Mean collective index {mean_score:.0f}/100",
            "confidence": "Heuristic — validate with learner feedback",
        })
    return suggestions
