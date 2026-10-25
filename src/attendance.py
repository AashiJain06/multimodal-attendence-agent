from __future__ import annotations

import os
import tempfile
from datetime import timedelta
from io import BytesIO

import cv2
import numpy as np
import pandas as pd
from PIL import Image


def _detector():
    # OpenCV's bundled Haar cascade is a lightweight offline baseline.
    path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(path)
    if detector.empty():
        raise RuntimeError("OpenCV Haar cascade could not be loaded.")
    return detector


def _detect(frame, detector):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(28, 28))
    return list(faces)


def analyze_photo(payload: bytes):
    image = Image.open(BytesIO(payload)).convert("RGB")
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    detector = _detector()
    faces = _detect(frame, detector)
    for i, (x, y, w, h) in enumerate(faces, start=1):
        cv2.rectangle(frame, (x, y), (x+w, y+h), (50, 180, 100), 2)
        cv2.putText(frame, f"Track {i}", (x, max(20, y-8)), cv2.FONT_HERSHEY_SIMPLEX, .55, (50,180,100), 2)
    rows = [{
        "Student ID": f"Track-{i}",
        "First Seen": "Single photo",
        "Last Seen": "Single photo",
        "Total Duration": "Unknown",
        "Presence (%)": None,
        "Status": "Manual review",
    } for i, _ in enumerate(faces, start=1)]
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), pd.DataFrame(rows, columns=["Student ID","First Seen","Last Seen","Total Duration","Presence (%)","Status"])


def analyze_video(payload: bytes, sample_every: int = 2, threshold: float = .70):
    suffix = ".mp4"
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(payload)
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise ValueError("Video codec could not be opened by OpenCV.")
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        duration = frame_count / fps if fps > 0 else 0
        if duration <= 0:
            raise ValueError("Video duration could not be determined.")
        detector = _detector()
        tracks = {}
        preview = None
        t = 0.0
        sample_every = max(1, int(sample_every))
        while t < duration:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, frame = cap.read()
            if not ok:
                t += sample_every
                continue
            if preview is None:
                preview = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2RGB)
            faces = _detect(frame, detector)
            # Lightweight centroid matching. Not biometric identification; IDs can switch in crowded scenes.
            centers = [(x+w/2, y+h/2, (x,y,w,h)) for x,y,w,h in faces]
            used = set()
            for cx, cy, rect in centers:
                best, best_dist = None, float("inf")
                for track_id, tr in tracks.items():
                    if track_id in used:
                        continue
                    px, py = tr["last_center"]
                    dist = ((cx-px)**2 + (cy-py)**2) ** .5
                    if dist < best_dist and dist < max(frame.shape[:2]) * .12:
                        best, best_dist = track_id, dist
                if best is None:
                    best = f"Track-{len(tracks)+1}"
                    tracks[best] = {"first": t, "last": t, "hits": 0, "last_center": (cx,cy)}
                tr = tracks[best]
                tr["last"] = t
                tr["hits"] += 1
                tr["last_center"] = (cx,cy)
                used.add(best)
            t += sample_every
        cap.release()
        sample_count = max(1, int(np.ceil(duration / sample_every)))
        rows = []
        for track_id, tr in tracks.items():
            pct = min(100.0, 100.0 * tr["hits"] / sample_count)
            rows.append({
                "Student ID": track_id,
                "First Seen": str(timedelta(seconds=int(tr["first"]))),
                "Last Seen": str(timedelta(seconds=int(tr["last"]))),
                "Total Duration": str(timedelta(seconds=max(0, int(tr["last"] - tr["first"])))),
                "Presence (%)": round(pct, 1),
                "Status": "Present" if pct >= threshold * 100 else "Absent",
            })
        df = pd.DataFrame(rows, columns=["Student ID","First Seen","Last Seen","Total Duration","Presence (%)","Status"])
        return df, preview
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def attendance_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
