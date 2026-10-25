from __future__ import annotations

import json
from datetime import datetime
import pandas as pd


def engagement_timeline(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy() if df is not None else pd.DataFrame()


def kpi_summary(data: dict) -> dict:
    attendance = data.get("attendance", pd.DataFrame())
    audio = data.get("audio", pd.DataFrame())
    engagement = data.get("engagement", pd.DataFrame())
    present = int((attendance["Status"] == "Present").sum()) if not attendance.empty and "Status" in attendance else 0
    total = len(attendance)
    mean_engagement = float(engagement["engagement_index"].mean()) if not engagement.empty else None
    discussion = int((audio["class"] == "Student Discussion / Verbal Interaction").sum()) if not audio.empty else 0
    return {
        "Tracked faces": str(total),
        "Present tracks": str(present),
        "Mean engagement": f"{mean_engagement:.0f}/100" if mean_engagement is not None else "—",
        "Discussion windows": str(discussion),
    }


def build_session_report(data: dict) -> dict:
    kpis = kpi_summary(data)
    attendance = data.get("attendance", pd.DataFrame())
    audio = data.get("audio", pd.DataFrame())
    engagement = data.get("engagement", pd.DataFrame())
    suggestions = data.get("suggestions", [])
    lines = [
        f"# Session report: {data.get('session_name', 'Classroom session')}",
        "",
        f"- Generated: {datetime.now().isoformat(timespec='minutes')}",
        f"- Session started: {data.get('started_at', 'Unknown')}",
        "",
        "## Key indicators",
    ]
    lines += [f"- **{key}:** {value}" for key, value in kpis.items()]
    if not audio.empty:
        lines += ["", "## Acoustic dynamics", f"- Analyzed windows: {len(audio)}"]
        counts = audio["class"].value_counts().to_dict()
        lines += [f"- {label}: {count}" for label, count in counts.items()]
    if not engagement.empty:
        lines += ["", "## Engagement", f"- Mean index: {engagement['engagement_index'].mean():.1f}/100",
                  f"- Lowest window: {engagement['engagement_index'].min():.1f}/100",
                  f"- Highest window: {engagement['engagement_index'].max():.1f}/100"]
    if suggestions:
        lines += ["", "## Suggested teaching actions"]
        lines += [f"- **{s['title']}** — {s['prompt']}" for s in suggestions]
    lines += ["", "## Educator reflection", data.get("notes", "") or "_No notes added._",
              "", "## Interpretation & limitations",
              "These outputs are heuristic estimates and may be inaccurate across room layouts, accents, microphones, lighting, seating positions, and accessibility needs. They are not validated measures of learning, attention, or identity. Review results with context and learner feedback."]
    serializable = {
        "session_name": data.get("session_name"),
        "started_at": data.get("started_at"),
        "kpis": kpis,
        "attendance": attendance.to_dict(orient="records") if not attendance.empty else [],
        "audio": audio.to_dict(orient="records") if not audio.empty else [],
        "engagement": engagement.to_dict(orient="records") if not engagement.empty else [],
        "suggestions": suggestions,
        "notes": data.get("notes", ""),
    }
    return {"markdown": "\n".join(lines), "data": serializable}
