# gap_batch.py
from __future__ import annotations
import re
import sys
import csv
import argparse
from pathlib import Path
from typing import Optional, Iterable, Tuple, List

from PIL import UnidentifiedImageError
from src.detect import detect_shelf_gaps  # import from your module
from tqdm.auto import tqdm

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

def _iter_images(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.suffix.lower() in IMAGE_EXTS and p.is_file():
            yield p

def _extract_sku(p: Path, sku_regex: Optional[str]) -> Optional[str]:
    name = p.stem
    if sku_regex:
        m = re.search(sku_regex, name)
        if m:
            return m.group(1) if m.groups() else m.group(0)
        return None
    # default heuristic: take leading token of filename (before first non-alnum/[_-])
    m = re.match(r"([A-Za-z0-9_-]+)", name)
    return m.group(1) if m else None

def batch_gap_scores(
    input_dir: Path,
    output_csv: Path,
    *,
    mode: str = "local",
    sku_regex: Optional[str] = None,
    max_side: int = 1024,
    tile: int = 48,
    uniform_thresh: float = 800.0,
    variance_ref: float = 5000.0,
    fail_on_no_sku: bool = False,
    show_progress: Optional[bool] = None,
) -> Tuple[int, int]:
    """
    Returns (processed_count, written_rows).
    """
    input_dir = Path(input_dir)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Tuple[str, float, str, str, str]] = []
    images = list(_iter_images(input_dir))
    auto_progress = (sys.stderr.isatty() and len(images) >= 50)
    use_progress = auto_progress if show_progress is None else bool(show_progress)
    iterator = tqdm(images, total=len(images), desc="Scoring", unit="img") if use_progress else images

    processed = 0
    for img_path in iterator:
        processed += 1
        sku = _extract_sku(img_path, sku_regex)
        if not sku:
            if fail_on_no_sku:
                raise ValueError(f"Could not extract SKU from filename: {img_path.name}")
            # write a row with empty sku so you can inspect later
            sku = ""
        try:
            res = detect_shelf_gaps(
                img_path,
                mode=mode, max_side=max_side, tile=tile,
                uniform_thresh=uniform_thresh, variance_ref=variance_ref,
            )
            rows.append((sku, res.gap_score, res.mode, res.notes, str(img_path)))
        except (UnidentifiedImageError, OSError) as e:
            rows.append((sku, 0.0, mode, f"Error: {e}", str(img_path)))
        except Exception as e:
            rows.append((sku, 0.0, mode, f"Unhandled error: {e}", str(img_path)))

    # Write CSV
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sku", "gap_score", "mode", "notes", "image_path"])
        w.writerows(rows)
    return processed, len(rows)

def main(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Batch shelf-gap scoring")
    ap.add_argument("input_dir", type=Path, help="Folder of images to process (recurses).")
    ap.add_argument("-o", "--output-csv", type=Path, default=Path("gap_scores.csv"))
    ap.add_argument("--mode", choices=["local", "global"], default="local")
    ap.add_argument("--sku-regex", type=str, default=None,
                    help=r"Regex to extract SKU from filename, e.g. '(\d{5})' or '(?i)^sku[_-]?([A-Z0-9-]+)'. "
                         "If omitted, uses a simple leading-token heuristic.")
    ap.add_argument("--max-side", type=int, default=1024)
    ap.add_argument("--tile", type=int, default=48)
    ap.add_argument("--uniform-thresh", type=float, default=800.0)
    ap.add_argument("--variance-ref", type=float, default=5000.0)
    ap.add_argument("--fail-on-no-sku", action="store_true",
                    help="Raise if a filename does not contain a parseable SKU.")
    # Progress control (tri-state): default auto; --progress to force on; --no-progress to force off
    ap.add_argument("--progress", dest="progress", action="store_true", help="Force-enable progress bar.")
    ap.add_argument("--no-progress", dest="progress", action="store_false", help="Disable progress bar.")
    ap.set_defaults(progress=None)
    args = ap.parse_args(argv)

    processed, written = batch_gap_scores(
        args.input_dir,
        args.output_csv,
        mode=args.mode,
        sku_regex=args.sku_regex,
        max_side=args.max_side,
        tile=args.tile,
        uniform_thresh=args.uniform_thresh,
        variance_ref=args.variance_ref,
        fail_on_no_sku=args.fail_on_no_sku,
        show_progress=args.progress,
    )
    print(f"Processed {processed} images; wrote {written} rows to {args.output_csv}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
    """Batch process images in a directory to compute shelf-gap scores and save to CSV."""