#!/usr/bin/env python
"""Test vision pipeline on sample screenshots using BLIP"""

import sys
import json
from pathlib import Path

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=" * 60)
print("VISION PIPELINE TEST - BLIP Captioning")
print("=" * 60)

# Find samples
samples_dir = Path(__file__).parent / "data" / "samples"
output_dir = Path(__file__).parent / "data" / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

# Get all PNG files
image_files = list(samples_dir.rglob("*.png"))
print(f"\nFound {len(image_files)} sample images")

# Test with first 5 images
test_images = image_files[:5]

print("\n" + "-" * 60)
print("Testing BLIP-2 (captioning)")
print("-" * 60)

try:
    import torch
    from transformers import BlipProcessor, BlipForConditionalGeneration
    from PIL import Image

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    # Load BLIP (smaller model, more stable)
    print("Loading BLIP model...")
    model_name = "Salesforce/blip-image-captioning-base"

    processor = BlipProcessor.from_pretrained(model_name)
    model = BlipForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    ).to(device)

    print("Model loaded!")

    results = []

    for img_path in test_images:
        print(f"\nAnalyzing: {img_path.parent.name}/{img_path.name}")

        image = Image.open(img_path).convert("RGB")

        # Unconditional captioning
        inputs = processor(images=image, return_tensors="pt").to(device, torch.float16 if device == "cuda" else torch.float32)

        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=50)

        caption = processor.decode(generated_ids[0], skip_special_tokens=True)
        print(f"  Caption: {caption}")

        # Conditional captioning (asking about the image)
        prompt = "a screenshot of"
        inputs = processor(images=image, text=prompt, return_tensors="pt").to(device, torch.float16 if device == "cuda" else torch.float32)

        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=50)

        detailed_caption = processor.decode(generated_ids[0], skip_special_tokens=True)
        print(f"  Detailed: {detailed_caption}")

        results.append({
            "image": str(img_path),
            "kic": img_path.parent.name,
            "name": img_path.stem,
            "caption": caption,
            "detailed_caption": detailed_caption,
        })

    # Save results
    output_path = output_dir / "vision_test_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n\nResults saved to: {output_path}")

except Exception as e:
    print(f"\nBLIP Error: {type(e).__name__}: {e}")
    print("Trying CLIP classification instead...")

print("\n" + "-" * 60)
print("Testing CLIP (classification)")
print("-" * 60)

try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    from PIL import Image

    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("Loading CLIP model...")
    model_name = "openai/clip-vit-base-patch32"

    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name).to(device)

    print("Model loaded!")

    # Visual register categories
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

    clip_results = []

    for img_path in test_images:
        print(f"\nClassifying: {img_path.parent.name}/{img_path.name}")

        image = Image.open(img_path).convert("RGB")

        inputs = processor(text=categories, images=image, return_tensors="pt", padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

        # Get top 3 predictions
        top3 = probs[0].topk(3)
        for i, (prob, idx) in enumerate(zip(top3.values, top3.indices)):
            cat = categories[idx]
            print(f"  {i+1}. {cat}: {prob.item():.1%}")

        clip_results.append({
            "image": str(img_path),
            "kic": img_path.parent.name,
            "name": img_path.stem,
            "classifications": {categories[idx]: float(probs[0][idx]) for idx in range(len(categories))},
            "top_category": categories[probs[0].argmax()],
        })

    # Save CLIP results
    output_path = output_dir / "clip_classification_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(clip_results, f, indent=2, ensure_ascii=False)

    print(f"\n\nCLIP results saved to: {output_path}")

except Exception as e:
    print(f"\nCLIP Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
