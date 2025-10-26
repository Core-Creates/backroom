#!/usr/bin/env python3
"""
Generate product image sets with either:
- SDXL (diffusers)  OR
- ChatGPT Images API (gpt-image-1)

Features:
- multiple angles/backgrounds
- N variants per combo (seeded)
- per-product folders + metadata (CSV + JSONL)
- optional montage grids

Requirements
-----------
SDXL path: diffusers, torch, Pillow
ChatGPT path: openai>=1.0.0 (Python SDK), Pillow
Set OPENAI_API_KEY for ChatGPT provider.

Docs:
- OpenAI Images API / gpt-image-1: platform.openai.com (see citations in chat)
"""

import argparse
import csv
import json
import os
import random
import re
import sys
from datetime import datetime
from typing import List, Optional

from PIL import Image

# --- OpenAI client (import lazily inside function if missing) ---
# from openai import OpenAI  # imported only when provider=="chatgpt"

# --- Diffusers (import lazily) ---
# from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
# import torch

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
}

# ---------- Prompt builder ----------
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

def slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")

def ensure_list_from_csvish(s: Optional[str], default: List[str]) -> List[str]:
    if not s:
        return default
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]

def parse_csv_or_yaml(batch_path: str) -> List[dict]:
    import csv as _csv, os as _os
    ext = _os.path.splitext(batch_path.lower())[1]
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
            reader = _csv.DictReader(f)
            for row in reader:
                items.append({"name": row.get("name", ""), "desc": row.get("desc", "")})
        return items
    else:
        raise ValueError("Batch file must be .csv, .yaml, or .yml")

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

# ---------- Providers ----------
def generate_diffusers(*, prompt: str, negative_prompt: str, out_path: str,
                       width: int, height: int, steps: int, guidance: float,
                       seed: Optional[int], model_id: str, refiner_id: Optional[str],
                       use_refiner: bool, shared_ctx: dict):
    # Lazy imports to keep ChatGPT path lightweight
    import torch
    from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if "pipe" not in shared_ctx:
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
        shared_ctx["pipe"] = pipe
        shared_ctx["device"] = device
    else:
        pipe = shared_ctx["pipe"]
        device = shared_ctx["device"]

    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    generator = torch.Generator(device=device).manual_seed(seed)

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
        if "refiner" not in shared_ctx:
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
            shared_ctx["refiner"] = refiner
        else:
            refiner = shared_ctx["refiner"]

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

    return {"seed": seed, "device": device, "model_id": model_id, "refiner_id": refiner_id if use_refiner else None}

def generate_chatgpt(*, prompt: str, negative_prompt: str, out_path: str,
                     size: str, quality: str, model: str, seed: Optional[int]):
    """
    Uses OpenAI Images API (gpt-image-1) to generate a PNG.
    NOTE: OpenAI doesn't support 'negative_prompt' param; we inline a short avoidance clause.
    """
    # Lazy import; uses OPENAI_API_KEY from env
    try:
        from openai import OpenAI
    except Exception as e:
        print("ERROR: openai SDK not installed. `pip install openai`", file=sys.stderr)
        raise

    client = OpenAI()

    # Make a single prompt string with a gentle avoidance hint
    neg = negative_prompt.strip().rstrip(".")
    avoid_clause = f" Avoid: {neg}." if neg else ""
    final_prompt = prompt + avoid_clause

    # Optional seeding: Images API supports a seed parameter on some releases; if not available, ignore gracefully.
    extra = {}
    if seed is not None:
        extra["seed"] = seed  # Silently ignored if model/version doesn’t support it.

    resp = client.images.generate(
        model=model,                 # e.g., "gpt-image-1"
        prompt=final_prompt,
        size=size,                   # e.g., "1024x1024" or "1152x1536"
        quality=quality,             # "standard" | "hd"
        **extra
    )
    b64 = resp.data[0].b64_json
    import base64
    img_bytes = base64.b64decode(b64)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(img_bytes)

    return {"seed": seed, "device": "openai_api", "model_id": model, "refiner_id": None}

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
    provider: str,
    openai_model: str,
    openai_size: str,
    openai_quality: str,
):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shared_ctx = {}  # holds diffusers pipelines

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
                    "model_id","refiner_id","device","timestamp","provider"
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
                        rnd = random.Random(f"{name}|{angle}|{bg}|{ts}")
                        use_seeds = [rnd.randint(0, 2**31 - 1) for _ in range(variants)]

                    # Build prompt once for this combo
                    prompt = build_prompt(name, desc, angle=angle, bg=bg)

                    # Generate images
                    combo_images = []
                    for vi, seed in enumerate(use_seeds[:variants]):
                        filename = f"{product_slug}_{combo_slug}_v{vi+1:02d}_s{seed}.png"
                        out_path = os.path.join(combo_dir, filename)

                        if provider == "diffusers":
                            info = generate_diffusers(
                                prompt=prompt,
                                negative_prompt=negative_prompt,
                                out_path=out_path,
                                width=width,
                                height=height,
                                steps=steps,
                                guidance=guidance,
                                seed=seed,
                                model_id=model_id,
                                refiner_id=refiner_id,
                                use_refiner=use_refiner,
                                shared_ctx=shared_ctx,
                            )
                        elif provider == "chatgpt":
                            # Map numeric width/height to closest OpenAI size string
                            # OpenAI accepts a few canonical sizes; if custom, pass f"{width}x{height}"
                            size = openai_size or f"{width}x{height}"
                            info = generate_chatgpt(
                                prompt=prompt,
                                negative_prompt=negative_prompt,
                                out_path=out_path,
                                size=size,
                                quality=openai_quality,
                                model=openai_model,
                                seed=seed,
                            )
                        else:
                            raise ValueError(f"Unknown provider: {provider}")

                        meta_out = {
                            "name": name,
                            "desc": desc,
                            "angle": angle,
                            "background": bg,
                            "variant_index": vi + 1,
                            "seed": info["seed"],
                            "width": width,
                            "height": height,
                            "steps": steps,
                            "guidance": guidance,
                            "path": out_path,
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "model_id": info["model_id"],
                            "refiner_id": info["refiner_id"],
                            "device": info["device"],
                            "timestamp": ts,
                            "provider": provider,
                        }
                        csv_writer.writerow(meta_out)
                        fjsonl.write(json.dumps(meta_out, ensure_ascii=False) + "\n")
                        try:
                            combo_images.append(Image.open(out_path))
                        except Exception:
                            pass

                    # Optional montage grid per combo
                    if grid and combo_images:
                        grid_img = make_grid(combo_images, cols=grid_cols)
                        grid_path = os.path.join(combo_dir, f"{product_slug}_{combo_slug}_GRID.png")
                        grid_img.save(grid_path)

        print(f"✅ Finished: {name} -> {prod_dir}")

# ---------- CLI ----------
def main():
    parser = argparse.ArgumentParser(description="Generate product image sets across angles/backgrounds/variants.")

    # Provider
    parser.add_argument("--provider", choices=["diffusers", "chatgpt"], default="diffusers",
                        help="Image generator backend")

    # Single product (or defaults applied to batch items)
    parser.add_argument("--name", help="Product name")
    parser.add_argument("--desc", help="Product description")

    # Batch file (CSV or YAML with fields: name, desc)
    parser.add_argument("--batch", help="Path to CSV or YAML listing products.")

    # Image + generation settings (diffusers)
    parser.add_argument("--width", type=int, default=896)
    parser.add_argument("--height", type=int, default=1152)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--guidance", type=float, default=6.5)
    parser.add_argument("--neg", default=DEFAULT_NEGATIVE, help="Negative prompt override.")

    # SDXL + refiner (diffusers)
    parser.add_argument("--model", default="stabilityai/stable-diffusion-xl-base-1.0")
    parser.add_argument("--refiner", default="stabilityai/stable-diffusion-xl-refiner-1.0")
    parser.add_argument("--no-refiner", action="store_true", help="Disable SDXL refiner pass.")

    # OpenAI Images (ChatGPT) flags
    parser.add_argument("--openai-model", default="gpt-image-1", help="OpenAI image model id")
    parser.add_argument("--openai-size", default="", help='Image size like "1024x1024" or leave blank to use WIDTHxHEIGHT')
    parser.add_argument("--openai-quality", default="standard", choices=["standard", "hd"], help="Image quality")

    # Set expansion controls
    parser.add_argument("--pack", default="catalog",
                        help="Preset pack name (e.g., catalog). Use 'custom' to supply --angles/--bgs.")
    parser.add_argument("--angles", default="", help="Comma-separated angles (used with --pack custom).")
    parser.add_argument("--bgs", default="", help="Comma-separated backgrounds (used with --pack custom).")
    parser.add_argument("--variants", type=int, default=3, help="Variants per angle/background combo.")
    parser.add_argument("--seeds", default=None, help="Comma-separated integer seeds for deterministic variants.")

    # Output controls
    parser.add_argument("--out", default="outputs", help="Root output directory for sets.")
    parser.add_argument("--grid", action="store_true", help="Save a montage grid per angle/background combo.")
    parser.add_argument("--grid-cols", type=int, default=3, help="Columns for montage grid.")

    args = parser.parse_args()

    # Handle pack presets
    if args.pack != "custom":
        if args.pack not in PACKS:
            print(f"ERROR: Unknown pack '{args.pack}'. Available: {', '.join(PACKS.keys())}", file=sys.stderr)
            sys.exit(2)
        pack = PACKS[args.pack]
        angles = pack["angles"]
        bgs = pack["bgs"]
    else:
        angles = ensure_list_from_csvish(args.angles, [])
        bgs = ensure_list_from_csvish(args.bgs, [])
        if not angles or not bgs:
            print("ERROR: In --pack custom mode you must provide both --angles and --bgs.", file=sys.stderr)
            sys.exit(2)

    # Collect products
    products: List[dict] = []
    if args.batch:
        batch_items = parse_csv_or_yaml(args.batch)
        for it in batch_items:
            if not it.get("name") or not it.get("desc"):
                continue
            products.append({"name": it["name"], "desc": it["desc"]})

    if args.name and args.desc:
        products.append({"name": args.name, "desc": args.desc})

    if not products:
        print("ERROR: Provide either --batch (CSV/YAML with name,desc) or --name and --desc.", file=sys.stderr)
        sys.exit(2)

    # Seeds
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
        provider=args.provider,
        openai_model=args.openai_model,
        openai_size=args.openai_size,
        openai_quality=args.openai_quality,
    )

if __name__ == "__main__":
    main()
