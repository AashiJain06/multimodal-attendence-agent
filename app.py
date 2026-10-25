from __future__ import annotations

import io
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.analytics import build_session_report, engagement_timeline, kpi_summary
from src.audio_engine import analyze_audio, audio_features_available
from src.attendance import analyze_photo, analyze_video, attendance_csv
from src.engagement import build_engagement_matrix, engagement_score
from src.suggestions import generate_suggestions
from src.styles import apply_styles

APP_NAME = "Multimodal Attendance & Engagement Agent"
st.set_page_config(page_title=APP_NAME, page_icon="🎓", layout="wide")
apply_styles()

if "session_data" not in st.session_state:
    st.session_state.session_data = {
        "session_name": "Classroom session",
        "started_at": datetime.now().isoformat(timespec="minutes"),
        "attendance": pd.DataFrame(),
        "audio": pd.DataFrame(),
        "engagement": pd.DataFrame(),
        "suggestions": [],
        "notes": "",
    }

data = st.session_state.session_data

with st.sidebar:
    st.markdown("## 🎓 Classroom Insights")
    st.caption("Local-first • educator-controlled • non-punitive")
    data["session_name"] = st.text_input("Session name", value=data["session_name"])
    st.divider()
    st.markdown("### Privacy controls")
    st.success("Processing runs on this app instance. Do not upload identifiable media unless you have consent.")
    st.caption("For strict offline use, run locally with network access disabled. Streamlit Community Cloud itself is not an offline edge device.")
    st.markdown("**Design principle**")
    st.caption("Use aggregated patterns to improve teaching, never as a definitive measure of an individual learner's attention.")

st.title("Multimodal Attendance & Engagement Agent")
st.markdown("A privacy-conscious classroom analytics prototype for attendance, acoustic dynamics, collective engagement, and teaching suggestions.")
st.info("**Responsible-use note:** face tracking and audio labels are fallible. Treat outputs as review aids, not disciplinary evidence. Obtain consent, follow institutional policy, and offer a non-camera alternative.")

tabs = st.tabs([
    "1 · Presence attendance",
    "2 · Acoustic dynamics",
    "3 · Multimodal engagement",
    "4 · Teaching suggestions",
    "5 · Session report",
])

with tabs[0]:
    st.subheader("Automated presence-based attendance")
    st.write("Upload a classroom video or photo. Video analysis samples frames locally; a photo only provides a single-moment observation and cannot establish sustained presence.")
    uploaded = st.file_uploader("Classroom video or photo", type=["mp4", "mov", "avi", "mkv", "jpg", "jpeg", "png"], key="attendance_upload")
    c1, c2, c3 = st.columns(3)
    with c1:
        threshold = st.slider("Presence threshold (% of sampled session)", 50, 100, 70)
    with c2:
        sample_every = st.slider("Sample every N seconds", 1, 10, 2)
    with c3:
        expected = st.number_input("Expected participants (optional)", min_value=0, max_value=500, value=0, step=1)
    if uploaded:
        is_photo = uploaded.type.startswith("image/")
        if st.button("Analyze media", type="primary", key="run_attendance"):
            try:
                payload = uploaded.getvalue()
                with st.spinner("Analyzing media on this app instance…"):
                    if is_photo:
                        frame, df = analyze_photo(payload)
                        st.image(frame, caption="Detected faces (single frame)", use_container_width=True)
                        st.warning("Single-photo analysis cannot determine first/last seen or sustained attendance. Review the result manually.")
                    else:
                        df, preview = analyze_video(payload, sample_every=sample_every, threshold=threshold / 100)
                        if preview is not None:
                            st.image(preview, caption="Sampled frame preview", use_container_width=True)
                    data["attendance"] = df
                st.success(f"Analysis complete: {len(df)} tracked face track(s).")
            except Exception as exc:
                st.error(f"Could not analyze this media: {exc}")
                st.caption("Try MP4/JPEG, reduce file size, or install the optional vision dependencies.")
    if not data["attendance"].empty:
        st.dataframe(data["attendance"], use_container_width=True, hide_index=True)
        st.download_button("Download attendance CSV", attendance_csv(data["attendance"]), "attendance_register.csv", "text/csv")
        st.caption("Track IDs are anonymous face tracks, not verified student identities. Map IDs to a roster only through a consent-based, educator-reviewed process.")
    else:
        st.caption("No attendance analysis yet. A webcam capture option can be added for local deployments; browser-hosted apps cannot reliably access a server-side webcam.")

with tabs[1]:
    st.subheader("Acoustic interaction & noise dynamics")
    st.write("Upload a short audio recording to estimate speech activity and acoustic energy in time windows. This baseline does not identify speakers or infer the content of speech.")
    audio_file = st.file_uploader("Audio file", type=["wav", "mp3", "m4a", "ogg", "flac"], key="audio_upload")
    a1, a2 = st.columns(2)
    with a1:
        window_seconds = st.slider("Window length (seconds)", 2, 15, 5)
    with a2:
        noise_threshold = st.slider("High ambient energy threshold", 0.05, 0.50, 0.22, 0.01)
    if audio_file and st.button("Analyze audio", type="primary"):
        try:
            with st.spinner("Extracting acoustic features…"):
                data["audio"] = analyze_audio(audio_file.getvalue(), audio_file.name, window_seconds, noise_threshold)
            st.success("Audio analysis complete.")
        except Exception as exc:
            st.error(f"Audio analysis failed: {exc}")
            st.caption("WAV is the most reliable input. MP3/M4A support may require FFmpeg.")
    if not data["audio"].empty:
        st.dataframe(data["audio"], use_container_width=True, hide_index=True)
        st.line_chart(data["audio"].set_index("time_seconds")[["rms_energy", "speech_ratio"]])
        st.download_button("Download acoustic CSV", data["audio"].to_csv(index=False).encode(), "acoustic_dynamics.csv", "text/csv")
    else:
        st.caption("Expected classes: Silence, Instructor Lecture (speech-dominant), Student Discussion / Verbal Interaction (speech with higher variability), and High Ambient Classroom Distraction. These are heuristic labels and need local calibration.")

with tabs[2]:
    st.subheader("Multimodal fusion & collective engagement")
    st.write("Combines coarse visual indicators (when available) with acoustic interaction features. The score is a pedagogical signal, not a validated psychological measurement.")
    col1, col2, col3 = st.columns(3)
    with col1:
        visual_attention = st.slider("Visual attentiveness estimate", 0, 100, 65)
    with col2:
        interaction = st.slider("Interaction level estimate", 0, 100, 45)
    with col3:
        posture = st.slider("Upright posture estimate", 0, 100, 70)
    if st.button("Build engagement timeline", type="primary"):
        try:
            data["engagement"] = build_engagement_matrix(data["audio"], visual_attention, interaction, posture)
        except Exception as exc:
            st.error(f"Could not build engagement timeline: {exc}")
    if not data["engagement"].empty:
        score = engagement_score(data["engagement"])
        st.metric("Collective engagement index", f"{score:.0f}/100")
        st.line_chart(engagement_timeline(data["engagement"]).set_index("time_label")[["engagement_index"]])
        st.dataframe(data["engagement"], use_container_width=True, hide_index=True)
        st.download_button("Download engagement matrix", data["engagement"].to_csv(index=False).encode(), "engagement_matrix.csv", "text/csv")
    else:
        st.caption("Use the controls as a transparent fallback if no visual/audio measurements are available. The score weights are documented in src/engagement.py.")

with tabs[3]:
    st.subheader("AI teaching suggestion engine")
    st.write("Rule-based, non-intrusive prompts for the educator. Suggestions are based on aggregate trends, not individual students.")
    if st.button("Generate teaching suggestions", type="primary"):
        data["suggestions"] = generate_suggestions(data["engagement"], data["audio"])
    if data["suggestions"]:
        for item in data["suggestions"]:
            with st.container(border=True):
                st.markdown(f"**{item['title']}**")
                st.write(item["prompt"])
                st.caption(f"Signal: {item['signal']} · Confidence: {item['confidence']}")
    else:
        st.info("No suggestions generated yet. Build an engagement timeline first, or generate suggestions to see baseline prompts.")

with tabs[4]:
    st.subheader("Session analytics & educator report")
    if data["engagement"].empty and data["attendance"].empty and data["audio"].empty:
        st.info("Run one or more analyses to populate the report. You can also add educator notes below.")
    kpis = kpi_summary(data)
    cols = st.columns(4)
    for col, (label, value) in zip(cols, kpis.items()):
        col.metric(label, value)
    data["notes"] = st.text_area("Educator reflection / context", value=data.get("notes", ""), placeholder="What worked well? What would you change next time?")
    report = build_session_report(data)
    st.markdown("#### Session summary")
    st.markdown(report["markdown"])
    st.download_button("Download session report (Markdown)", report["markdown"].encode("utf-8"), "session_summary.md", "text/markdown")
    st.download_button("Download all results (JSON)", json.dumps(report["data"], indent=2, default=str).encode("utf-8"), "session_results.json", "application/json")

st.divider()
st.caption("Prototype status: production hardening still requires classroom validation, consent workflow, accessibility review, threat modeling, and testing on target hardware.")
