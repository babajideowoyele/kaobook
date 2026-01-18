#!/usr/bin/env python
"""Analyze all sample screenshots and prepare data for UI"""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=" * 60)
print("FULL VISUAL ANALYSIS PIPELINE")
print("=" * 60)

# Paths
samples_dir = Path(__file__).parent / "data" / "samples"
output_dir = Path(__file__).parent / "data" / "outputs"
ui_dir = Path(__file__).parent / "ui"
output_dir.mkdir(parents=True, exist_ok=True)
ui_dir.mkdir(parents=True, exist_ok=True)

# Get all PNG files
image_files = sorted(samples_dir.rglob("*.png"))
print(f"\nFound {len(image_files)} sample images")

# Import models
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")

# Load BLIP
print("\nLoading BLIP model...")
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
).to(device)

# Load CLIP
print("Loading CLIP model...")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)

# Visual register categories (Kress & van Leeuwen inspired)
categories = [
    "website homepage with navigation menu",
    "team photo with people",
    "technology or product showcase",
    "abstract graphic design",
    "infographic or diagram",
    "event or conference photo",
    "logo and branding",
    "text-heavy document",
]

# Coding orientations
coding_orientations = [
    "naturalistic photograph",
    "technological interface",
    "sensory artistic image",
    "abstract geometric design",
]

# Process all images
print("\n" + "-" * 60)
print("Analyzing images...")
print("-" * 60)

results = []

for i, img_path in enumerate(image_files):
    print(f"\n[{i+1}/{len(image_files)}] {img_path.parent.name}/{img_path.name}")

    image = Image.open(img_path).convert("RGB")
    width, height = image.size

    # BLIP caption
    inputs = blip_processor(images=image, return_tensors="pt").to(device, torch.float16 if device == "cuda" else torch.float32)
    with torch.no_grad():
        generated_ids = blip_model.generate(**inputs, max_new_tokens=50)
    caption = blip_processor.decode(generated_ids[0], skip_special_tokens=True)
    print(f"  Caption: {caption}")

    # CLIP classification
    inputs = clip_processor(text=categories, images=image, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = clip_model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)

    category_scores = {cat: float(probs[0][j]) for j, cat in enumerate(categories)}
    top_category = max(category_scores, key=category_scores.get)

    # CLIP coding orientation
    inputs = clip_processor(text=coding_orientations, images=image, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = clip_model(**inputs)
        orient_probs = outputs.logits_per_image.softmax(dim=1)

    orientation_scores = {orient: float(orient_probs[0][j]) for j, orient in enumerate(coding_orientations)}
    top_orientation = max(orientation_scores, key=orientation_scores.get)

    print(f"  Category: {top_category} ({category_scores[top_category]:.1%})")
    print(f"  Orientation: {top_orientation} ({orientation_scores[top_orientation]:.1%})")

    results.append({
        "id": i,
        "filename": img_path.name,
        "name": img_path.stem.replace("_", " "),
        "kic": img_path.parent.name.replace("_", " "),
        "path": f"../data/samples/{img_path.parent.name}/{img_path.name}",
        "width": width,
        "height": height,
        "caption": caption,
        "category": top_category,
        "category_scores": category_scores,
        "coding_orientation": top_orientation,
        "orientation_scores": orientation_scores,
    })

# Compute statistics
print("\n" + "-" * 60)
print("Computing statistics...")
print("-" * 60)

kic_counts = defaultdict(int)
category_counts = defaultdict(int)
orientation_counts = defaultdict(int)

for r in results:
    kic_counts[r["kic"]] += 1
    category_counts[r["category"]] += 1
    orientation_counts[r["coding_orientation"]] += 1

stats = {
    "total_images": len(results),
    "by_kic": dict(kic_counts),
    "by_category": dict(category_counts),
    "by_orientation": dict(orientation_counts),
}

print(f"\nBy KIC: {dict(kic_counts)}")
print(f"By Category: {dict(category_counts)}")
print(f"By Orientation: {dict(orientation_counts)}")

# Save results
output_data = {
    "images": results,
    "statistics": stats,
    "categories": categories,
    "coding_orientations": coding_orientations,
}

# Save to outputs
output_path = output_dir / "visual_analysis_full.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)
print(f"\nSaved full results to: {output_path}")

# Save to UI folder for web access
ui_data_path = ui_dir / "visual_data.json"
with open(ui_data_path, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)
print(f"Saved UI data to: {ui_data_path}")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
