#!/usr/bin/env python3
"""
Generate product image sets with SDXL (+ optional refiner), across:
- multiple angles
- multiple backgrounds
- multiple variants per combo (seeded for reproducibility)

Outputs:
- images in per-product folders with tidy subfolders
- metadata.csv and metadata.jsonl with full parameters per image
- optional per-combo montage grid

Quick examples
-------------
# 1) One product, 4 angles x 2 backgrounds x 3 variants each (24 images total)
python generate_set.py \
  --name "Aurora Glass Kettle" \
  --desc "borosilicate glass electric kettle with matte black base and cool-touch handle" \
  --angles "front, three-quarter view, side, top-down" \
  --bgs "seamless white backdrop, light gray gradient" \
  --variants 3

# 2) Batch from YAML/CSV (fields: name, desc)
python generate_set.py --batch products.yaml --variants 2 --angles "front, three-quarter view" --grid

# 3) Fixed seed list (overrides random), good for deterministic reruns
python generate_set.py --name "Carbon Mug" --desc "matte ceramic travel mug" --seeds 111,222,333

Notes
-----
- Requires: diffusers, torch, PIL (Pillow)
- CUDA if available; falls back to CPU.
"""

import argparse
import csv
import json
import os
import random
import re
import sys
import time
from datetime import datetime
from typing import Iterable, List, Optional, Tuple

from PIL import Image

import torch
from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler

# ---------- Preset packs ----------
PACKS = {
    "catalog": {
        "angles": [
            "front",
            "three-quarter view",
            "side",
            "top-down"
        ],
        "bgs": [
            "seamless white backdrop",
            "light gray gradient",
            "white sweep with soft shadow",
            "white backdrop with subtle mirrored reflection"
        ],
    },
    # room for more later: "lifestyle_clean", "shadow_play", etc.
}

# ---------- Prompt builder (unchanged core style) ----------
def build_prompt(name: str, description: str, angle="three-quarter view", bg="seamless white backdrop"):
    name = name.strip()
    description = re.sub(r"\s+", " ", description.strip())

    core = (
        f"{name}, {description}. Ultra-detailed product photo on {bg}, "
        f"{angle}, soft studio lighting, realistic materials, true-to-life colors, "
        f"high dynamic range, finely textured surfaces, crisp focus, subtle shadows, "
        f"commercial catalog style, no people."
    )

    style_boosters = [
        "photorealistic", "studio photography", "8k uhd", "dslr", "polarizing filter",
        "product staging", "ray-traced reflections", "volumetric softbox lighting"
    ]
    return f"{core}, " + ", ".join(style_boosters)

DEFAULT_NEGATIVE = (
    "lowres, blurry, soft focus, overexposed, underexposed, noise, "
    "watermark, text, logo artifacts, duplicate objects, warped geometry, "
    "bad proportions, extra parts, cut off, jpeg artifacts, unrealistic materials, "
    "hands, people"
)

# ---------- Core single-image generator (kept very close to yours) ----------
def generate(
    product_name: str,
    product_desc: str,
    out_path: str,
    width: int = 896,
    height: int = 1152,
    steps: int = 30,
    guidance: float = 6.5,
    seed: Optional[int] = None,
    negative_prompt: str = DEFAULT_NEGATIVE,
    model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
    refiner_id: Optional[str] = "stabilityai/stable-diffusion-xl-refiner-1.0",
    use_refiner: bool = True,
    angle: str = "three-quarter view",
    bg: str = "seamless white backdrop",
    shared_pipe: Optional[DiffusionPipeline] = None,
    shared_refiner: Optional[DiffusionPipeline] = None,
):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    generator = torch.Generator(device=device).manual_seed(seed)

    prompt = build_prompt(product_name, product_desc, angle=angle, bg=bg)

    # Reuse loaded pipelines when batching for speed/memory
    pipe = shared_pipe
    if pipe is None:
        pipe = DiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            use_safetensors=True,
        )
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        pipe = pipe.to(device)
        if device == "cuda":
            pipe.enable_model_cpu_offload()
            pipe.enable_vae_tiling()

    base = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=steps,
        guidance_scale=guidance,
        width=width,
        height=height,
        generator=generator,
    ).images[0]

    if use_refiner and refiner_id:
        refiner = shared_refiner
        if refiner is None:
            refiner = DiffusionPipeline.from_pretrained(
                refiner_id,
                text_encoder_2=pipe.text_encoder_2,
                vae=pipe.vae,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                use_safetensors=True,
            )
            refiner.scheduler = DPMSolverMultistepScheduler.from_config(refiner.scheduler.config)
            refiner = refiner.to(device)
            if device == "cuda":
                refiner.enable_model_cpu_offload()
                refiner.enable_vae_tiling()

        base = refiner(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=base,
            num_inference_steps=max(10, steps // 2),
            guidance_scale=max(4.5, guidance - 2.0),
            generator=generator,
        ).images[0]

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    base.save(out_path)

    return {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": seed,
        "steps": steps,
        "guidance": guidance,
        "size": (width, height),
        "path": out_path,
        "angle": angle,
        "background": bg,
        "model_id": model_id,
        "refiner_id": refiner_id if use_refiner else None,
        "device": device,
    }

# ---------- Helpers ----------
def slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")

def parse_csv_or_yaml(batch_path: str) -> List[dict]:
    ext = os.path.splitext(batch_path.lower())[1]
    if ext in [".yaml", ".yml"]:
        try:
            import yaml
        except ImportError:
            print("ERROR: pyyaml not installed. `pip install pyyaml` or use CSV.", file=sys.stderr)
            sys.exit(2)
        with open(batch_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, list):
            raise ValueError("YAML batch must be a list of items with fields: name, desc")
        return data
    elif ext == ".csv":
        items = []
        with open(batch_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append({"name": row.get("name", ""), "desc": row.get("desc", "")})
        return items
    else:
        raise ValueError("Batch file must be .csv, .yaml, or .yml")

def ensure_list_from_csvish(s: Optional[str], default: List[str]) -> List[str]:
    if not s:
        return default
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]

def make_grid(images: List[Image.Image], cols: int) -> Image.Image:
    if not images:
        raise ValueError("No images for grid")
    w, h = images[0].size
    rows = (len(images) + cols - 1) // cols
    grid = Image.new("RGB", (cols * w, rows * h), color=(255, 255, 255))
    for idx, img in enumerate(images):
        r = idx // cols
        c = idx % cols
        grid.paste(img.resize((w, h)), (c * w, r * h))
    return grid

# ---------- Batch set builder ----------
def generate_set(
    products: List[dict],
    width: int,
    height: int,
    steps: int,
    guidance: float,
    negative_prompt: str,
    model_id: str,
    refiner_id: Optional[str],
    use_refiner: bool,
    angles: List[str],
    bgs: List[str],
    variants: int,
    seeds: Optional[List[int]],
    out_root: str,
    grid: bool,
    grid_cols: int,
):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Prepare reusable pipelines
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipe = DiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=True,
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(device)
    if device == "cuda":
        pipe.enable_model_cpu_offload()
        pipe.enable_vae_tiling()

    refiner = None
    if use_refiner and refiner_id:
        refiner = DiffusionPipeline.from_pretrained(
            refiner_id,
            text_encoder_2=pipe.text_encoder_2,
            vae=pipe.vae,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            use_safetensors=True,
        )
        refiner.scheduler = DPMSolverMultistepScheduler.from_config(refiner.scheduler.config)
        refiner = refiner.to(device)
        if device == "cuda":
            refiner.enable_model_cpu_offload()
            refiner.enable_vae_tiling()

    for item in products:
        name = item["name"].strip()
        desc = item["desc"].strip()
        product_slug = slugify(name)
        prod_dir = os.path.join(out_root, f"{product_slug}_{ts}")
        os.makedirs(prod_dir, exist_ok=True)

        # Prepare metadata files
        meta_csv = os.path.join(prod_dir, "metadata.csv")
        meta_jsonl = os.path.join(prod_dir, "metadata.jsonl")
        csv_written_header = os.path.exists(meta_csv)

        with open(meta_csv, "a", newline="", encoding="utf-8") as fcsv, \
             open(meta_jsonl, "a", encoding="utf-8") as fjsonl:

            csv_writer = csv.DictWriter(
                fcsv,
                fieldnames=[
                    "name","desc","angle","background","variant_index","seed",
                    "width","height","steps","guidance","path","prompt","negative_prompt",
                    "model_id","refiner_id","device","timestamp"
                ]
            )
            if not csv_written_header:
                csv_writer.writeheader()

            for angle in angles:
                for bg in bgs:
                    combo_slug = f"{slugify(angle)}__{slugify(bg)}"
                    combo_dir = os.path.join(prod_dir, combo_slug)
                    os.makedirs(combo_dir, exist_ok=True)

                    # Decide seeds list
                    if seeds:
                        use_seeds = seeds
                    else:
                        # Stable, but random per combo
                        rnd = random.Random(f"{name}|{angle}|{bg}|{ts}")
                        use_seeds = [rnd.randint(0, 2**31 - 1) for _ in range(variants)]

                    # Generate images
                    combo_images = []
                    for vi, seed in enumerate(use_seeds[:variants]):
                        filename = f"{product_slug}_{combo_slug}_v{vi+1:02d}_s{seed}.png"
                        out_path = os.path.join(combo_dir, filename)
                        meta = generate(
                            product_name=name,
                            product_desc=desc,
                            out_path=out_path,
                            width=width,
                            height=height,
                            steps=steps,
                            guidance=guidance,
                            seed=seed,
                            negative_prompt=negative_prompt,
                            model_id=model_id,
                            refiner_id=refiner_id,
                            use_refiner=use_refiner,
                            angle=angle,
                            bg=bg,
                            shared_pipe=pipe,
                            shared_refiner=refiner,
                        )
                        meta_out = {
                            "name": name,
                            "desc": desc,
                            "angle": angle,
                            "background": bg,
                            "variant_index": vi + 1,
                            "seed": seed,
                            "width": width,
                            "height": height,
                            "steps": steps,
                            "guidance": guidance,
                            "path": meta["path"],
                            "prompt": meta["prompt"],
                            "negative_prompt": meta["negative_prompt"],
                            "model_id": meta["model_id"],
                            "refiner_id": meta["refiner_id"],
                            "device": meta["device"],
                            "timestamp": ts,
                        }
                        csv_writer.writerow(meta_out)
                        fjsonl.write(json.dumps(meta_out, ensure_ascii=False) + "\n")
                        combo_images.append(Image.open(meta["path"]))

                    # Optional montage grid per combo
                    if grid and combo_images:
                        grid_img = make_grid(combo_images, cols=grid_cols)
                        grid_path = os.path.join(combo_dir, f"{product_slug}_{combo_slug}_GRID.png")
                        grid_img.save(grid_path)

        print(f"✅ Finished: {name} -> {prod_dir}")

# ---------- CLI ----------
def main():
    parser = argparse.ArgumentParser(description="Generate product image sets across angles/backgrounds/variants.")
    # Single product (or defaults applied to batch items)
    parser.add_argument("--name", help="Product name")
    parser.add_argument("--desc", help="Product description")

    # Batch file (CSV or YAML with fields: name, desc)
    parser.add_argument("--batch", help="Path to CSV or YAML listing products.")

    # Image + generation settings
    parser.add_argument("--width", type=int, default=896)
    parser.add_argument("--height", type=int, default=1152)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--guidance", type=float, default=6.5)
    parser.add_argument("--neg", default=DEFAULT_NEGATIVE, help="Negative prompt override.")

    # SDXL + refiner
    parser.add_argument("--model", default="stabilityai/stable-diffusion-xl-base-1.0")
    parser.add_argument("--refiner", default="stabilityai/stable-diffusion-xl-refiner-1.0")
    parser.add_argument("--no-refiner", action="store_true", help="Disable SDXL refiner pass.")

    # Set expansion controls
    parser.add_argument("--angles", default="three-quarter view, front, side, top-down",
                        help="Comma-separated list of angles.")
    parser.add_argument("--bgs", default="seamless white backdrop, light gray gradient",
                        help="Comma-separated list of backgrounds.")
    parser.add_argument("--variants", type=int, default=3, help="Variants per angle/background combo.")
    parser.add_argument("--seeds", default=None, help="Comma-separated integer seeds to force deterministic variants.")

    # Output controls
    parser.add_argument("--out", default="outputs", help="Root output directory for sets.")
    parser.add_argument("--grid", action="store_true", help="Save a montage grid per angle/background combo.")
    parser.add_argument("--grid-cols", type=int, default=3, help="Columns for montage grid.")

    args = parser.parse_args()

    # Collect products
    products: List[dict] = []
    if args.batch:
        batch_items = parse_csv_or_yaml(args.batch)
        for it in batch_items:
            if not it.get("name") or not it.get("desc"):
                continue
            products.append({"name": it["name"], "desc": it["desc"]})

    # Allow single product without batch
    if args.name and args.desc:
        products.append({"name": args.name, "desc": args.desc})

    if not products:
        print("ERROR: Provide either --batch (CSV/YAML with name,desc) or --name and --desc.", file=sys.stderr)
        sys.exit(2)

    angles = ensure_list_from_csvish(args.angles, ["three-quarter view"])
    bgs = ensure_list_from_csvish(args.bgs, ["seamless white backdrop"])

    seeds = None
    if args.seeds:
        try:
            seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
        except ValueError:
            print("ERROR: --seeds must be comma-separated integers", file=sys.stderr)
            sys.exit(2)

    use_refiner = not args.no_refiner

    generate_set(
        products=products,
        width=args.width,
        height=args.height,
        steps=args.steps,
        guidance=args.guidance,
        negative_prompt=args.neg,
        model_id=args.model,
        refiner_id=args.refiner,
        use_refiner=use_refiner,
        angles=angles,
        bgs=bgs,
        variants=args.variants,
        seeds=seeds,
        out_root=args.out,
        grid=args.grid,
        grid_cols=args.grid_cols,
    )

if __name__ == "__main__":
    main()
