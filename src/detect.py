from pathlib import Path
from PIL import Image, ImageStat

# Lightweight demo: use image brightness variance as a proxy gap score.
# In the real system, replace with a YOLO/Segment-Anything pipeline.

def detect_shelf_gaps(image_path: Path):
    try:
        im = Image.open(image_path).convert("L")
        stat = ImageStat.Stat(im)
        # Heuristic: lower variance might indicate large uniform gaps; scale to 0..1
        variance = stat.var[0]
        gap_score = max(0.0, min(1.0, 1.0 - (variance / 5000.0)))
        notes = "Low-variance region may indicate empty facings." if gap_score > 0.6 else "No strong gap signal."
        return {"gap_score": round(gap_score, 3), "notes": notes}
    except Exception as e:
        return {"gap_score": 0.0, "notes": f"Error processing image: {e}"}
