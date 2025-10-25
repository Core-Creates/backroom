from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Union, IO, Literal, Optional

import io
import numpy as np
from PIL import Image, ImageOps

@dataclass(frozen=True)
class GapResult:
    gap_score: float          # 0..1 (higher => more likely gaps)
    mode: Literal["global", "local"]
    notes: str

ImageInput = Union[str, Path, bytes, IO[bytes]]

def _load_gray(im_input: ImageInput, max_side: Optional[int] = 1024) -> Image.Image:
    """Load as grayscale, apply EXIF transpose, optionally downscale to speed up."""
    if isinstance(im_input, (str, Path)):
        im = Image.open(im_input)
    elif isinstance(im_input, bytes):
        im = Image.open(io.BytesIO(im_input))
    else:
        im = Image.open(im_input)

    im = ImageOps.exif_transpose(im).convert("L")  # grayscale
    if max_side:
        w, h = im.size
        scale = max(w, h) / float(max_side)
        if scale > 1.0:
            im = im.resize((int(round(w / scale)), int(round(h / scale))), Image.BILINEAR)
    return im

def detect_shelf_gaps(
    image: ImageInput,
    *,
    mode: Literal["global", "local"] = "local",
    variance_ref: float = 5000.0,    # reference for global variance mapping
    tile: int = 48,                  # tile size (pixels) for local mode
    uniform_thresh: float = 800.0,   # per-tile variance below this = “uniform”
    max_side: Optional[int] = 1024,  # downscale for perf; None to disable
) -> GapResult:
    """
    Lightweight shelf-gap proxy.

    Modes
    -----
    - global:      gap_score = 1 - clip(var / variance_ref, 0, 1)
                   (low global variance ⇒ big uniform region ⇒ potential gaps)
    - local:       split image into tiles; gap_score = fraction of tiles with
                   variance < uniform_thresh (uniform tiles ≈ empty facings)

    Parameters
    ----------
    image : str | Path | bytes | file-like
        Input image.
    mode : "global" | "local"
        Heuristic to use. "local" is more informative for shelf scenarios.
    variance_ref : float
        Normalizer for global variance (bigger → lower scores).
    tile : int
        Tile size for local variance (pixels).
    uniform_thresh : float
        Per-tile variance threshold to call a tile “uniform”.
    max_side : int | None
        If set, downscales longest side to this many pixels before analysis.

    Returns
    -------
    GapResult
        gap_score in [0,1], chosen mode, and a short note.
    """
    try:
        im = _load_gray(image, max_side=max_side)
        arr = np.asarray(im, dtype=np.float32)

        if mode == "global":
            variance = float(arr.var())
            # Map variance to 0..1 (inverse: low variance -> high gap_score)
            score = 1.0 - min(1.0, max(0.0, variance / variance_ref))
            notes = f"global var={variance:.1f} (ref={variance_ref:g})"
            return GapResult(gap_score=round(score, 3), mode=mode, notes=notes)

        # local mode
        H, W = arr.shape
        th = max(8, int(tile))  # guard tiny tiles
        # Crop so that we can reshape cleanly into tiles
        Hc, Wc = H - (H % th), W - (W % th)
        if Hc <= 0 or Wc <= 0:
            # fallback to global if image is too small
            variance = float(arr.var())
            score = 1.0 - min(1.0, max(0.0, variance / variance_ref))
            notes = f"fallback-global (image too small), var={variance:.1f}"
            return GapResult(gap_score=round(score, 3), mode="global", notes=notes)

        tiles = arr[:Hc, :Wc].reshape(Hc // th, th, Wc // th, th).swapaxes(1, 2)  # [Ty, Tx, th, th]
        # Per-tile variance
        tvar = tiles.reshape(tiles.shape[0], tiles.shape[1], -1).var(axis=-1)
        uniform_mask = (tvar < uniform_thresh)
        frac_uniform = float(uniform_mask.mean())
        # Higher fraction of low-variance tiles ⇒ higher gap_score
        score = max(0.0, min(1.0, frac_uniform))
        tiles_total = tvar.size
        tiles_uniform = int(uniform_mask.sum())
        notes = f"local tiles={tiles_total}, uniform={tiles_uniform} ({frac_uniform:.2%}), thresh={uniform_thresh:g}"

        return GapResult(gap_score=round(score, 3), mode="local", notes=notes)

    except Exception as e:
        return GapResult(gap_score=0.0, mode=mode, notes=f"Error processing image: {e}")
    """Detect shelf gaps in an image using simple variance-based heuristics."""