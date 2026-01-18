"""
Vision Model Pipeline for Visual Materials Analysis.

Provides automated visual feature extraction using multimodal LLMs:
- Florence-2: Microsoft's unified vision model for captioning, OCR, detection
- BLIP-2: Salesforce's image-text model for detailed captions
- CLIP: OpenAI's vision-language model for similarity and classification

These models augment manual Kress & van Leeuwen coding by providing:
1. Automatic image captioning
2. Object and person detection
3. OCR for text extraction from screenshots
4. Visual similarity for clustering
"""

from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
from tqdm import tqdm

# Conditional imports
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@dataclass
class VisualFeatures:
    """Extracted visual features from an image."""
    image_path: str
    caption: str = ""
    detailed_caption: str = ""
    ocr_text: str = ""
    detected_objects: List[Dict[str, Any]] = field(default_factory=list)
    detected_faces: int = 0
    scene_type: str = ""
    dominant_colors: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'image_path': self.image_path,
            'caption': self.caption,
            'detailed_caption': self.detailed_caption,
            'ocr_text': self.ocr_text,
            'detected_objects': self.detected_objects,
            'detected_faces': self.detected_faces,
            'scene_type': self.scene_type,
            'dominant_colors': self.dominant_colors,
            'has_embedding': self.embedding is not None,
        }


class Florence2Analyzer:
    """
    Visual analysis using Microsoft Florence-2.

    Florence-2 is a unified vision model that can perform:
    - Image captioning (brief and detailed)
    - OCR (text extraction)
    - Object detection
    - Dense region captioning
    - Visual grounding

    Model: microsoft/Florence-2-large
    Size: ~1.5GB
    """

    def __init__(
        self,
        model_name: str = "microsoft/Florence-2-large",
        device: str = None,
        use_flash_attention: bool = False,
    ):
        if not HAS_TORCH:
            raise ImportError("PyTorch required. Install with: pip install torch")

        from transformers import AutoProcessor, AutoModelForCausalLM

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading Florence-2 on {self.device}...")

        # Load model
        self.processor = AutoProcessor.from_pretrained(
            model_name, trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        ).to(self.device)

        print("Florence-2 loaded successfully")

    def _run_task(self, image: 'Image.Image', task: str, text_input: str = None) -> str:
        """Run a Florence-2 task on an image."""
        if text_input:
            prompt = f"<{task}>{text_input}"
        else:
            prompt = f"<{task}>"

        inputs = self.processor(text=prompt, images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                num_beams=3,
            )

        generated_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=False
        )[0]

        # Parse the output
        parsed = self.processor.post_process_generation(
            generated_text,
            task=f"<{task}>",
            image_size=(image.width, image.height)
        )

        return parsed

    def analyze(self, image_path: str) -> VisualFeatures:
        """Extract visual features from an image."""
        image = Image.open(image_path).convert("RGB")

        features = VisualFeatures(image_path=str(image_path))

        # Caption
        try:
            result = self._run_task(image, "CAPTION")
            features.caption = result.get("<CAPTION>", "")
        except Exception as e:
            print(f"Caption failed: {e}")

        # Detailed caption
        try:
            result = self._run_task(image, "DETAILED_CAPTION")
            features.detailed_caption = result.get("<DETAILED_CAPTION>", "")
        except Exception as e:
            print(f"Detailed caption failed: {e}")

        # OCR
        try:
            result = self._run_task(image, "OCR")
            features.ocr_text = result.get("<OCR>", "")
        except Exception as e:
            print(f"OCR failed: {e}")

        # Object detection
        try:
            result = self._run_task(image, "OD")
            bboxes = result.get("<OD>", {})
            if bboxes and "labels" in bboxes:
                features.detected_objects = [
                    {"label": label, "bbox": bbox}
                    for label, bbox in zip(bboxes["labels"], bboxes.get("bboxes", []))
                ]
                # Count faces/people
                features.detected_faces = sum(
                    1 for obj in features.detected_objects
                    if obj["label"].lower() in ["person", "face", "human"]
                )
        except Exception as e:
            print(f"Object detection failed: {e}")

        return features

    def batch_analyze(
        self,
        image_paths: List[str],
        output_path: str = None
    ) -> List[VisualFeatures]:
        """Analyze multiple images."""
        results = []

        for path in tqdm(image_paths, desc="Analyzing images"):
            try:
                features = self.analyze(path)
                results.append(features)
            except Exception as e:
                print(f"Failed to analyze {path}: {e}")
                results.append(VisualFeatures(image_path=str(path)))

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump([r.to_dict() for r in results], f, indent=2)
            print(f"Saved results to {output_path}")

        return results


class CLIPAnalyzer:
    """
    Visual analysis using OpenAI CLIP.

    CLIP provides:
    - Image embeddings for similarity search
    - Zero-shot classification against text labels
    - Visual-semantic similarity scoring
    """

    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        device: str = None,
    ):
        if not HAS_TORCH:
            raise ImportError("PyTorch required. Install with: pip install torch")

        from transformers import CLIPProcessor, CLIPModel

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading CLIP on {self.device}...")

        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)

        print("CLIP loaded successfully")

    def get_embedding(self, image_path: str) -> List[float]:
        """Get image embedding vector."""
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            embeddings = self.model.get_image_features(**inputs)

        return embeddings[0].cpu().numpy().tolist()

    def classify(
        self,
        image_path: str,
        labels: List[str],
    ) -> Dict[str, float]:
        """Zero-shot classify image against text labels."""
        image = Image.open(image_path).convert("RGB")

        inputs = self.processor(
            text=labels,
            images=image,
            return_tensors="pt",
            padding=True,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

        return {label: float(prob) for label, prob in zip(labels, probs[0])}

    def classify_visual_register(self, image_path: str) -> Dict[str, float]:
        """Classify image according to visual register categories."""
        # Kress & van Leeuwen inspired categories
        categories = [
            # Coding orientations
            "naturalistic photograph with realistic colors",
            "technological diagram or interface",
            "abstract graphic design",
            "sensory artistic image",

            # Content types
            "people in professional setting",
            "technology and equipment",
            "nature and environment",
            "architectural or urban scene",

            # Social distance
            "close-up portrait",
            "group interaction",
            "distant overview scene",
        ]

        return self.classify(image_path, categories)


class VisualPipeline:
    """
    Complete visual analysis pipeline.

    Combines multiple vision models for comprehensive analysis:
    1. Florence-2 for captioning and OCR
    2. CLIP for embeddings and classification
    3. Face detection for people analysis
    """

    def __init__(
        self,
        use_florence: bool = True,
        use_clip: bool = True,
        device: str = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.florence = None
        self.clip = None

        if use_florence:
            try:
                self.florence = Florence2Analyzer(device=self.device)
            except Exception as e:
                print(f"Could not load Florence-2: {e}")

        if use_clip:
            try:
                self.clip = CLIPAnalyzer(device=self.device)
            except Exception as e:
                print(f"Could not load CLIP: {e}")

    def analyze(self, image_path: str) -> VisualFeatures:
        """Run full analysis pipeline on image."""
        features = VisualFeatures(image_path=str(image_path))

        # Florence-2 analysis
        if self.florence:
            try:
                florence_features = self.florence.analyze(image_path)
                features.caption = florence_features.caption
                features.detailed_caption = florence_features.detailed_caption
                features.ocr_text = florence_features.ocr_text
                features.detected_objects = florence_features.detected_objects
                features.detected_faces = florence_features.detected_faces
            except Exception as e:
                print(f"Florence-2 analysis failed: {e}")

        # CLIP classification
        if self.clip:
            try:
                classification = self.clip.classify_visual_register(image_path)
                # Get top scene type
                features.scene_type = max(classification, key=classification.get)
                # Get embedding
                features.embedding = self.clip.get_embedding(image_path)
            except Exception as e:
                print(f"CLIP analysis failed: {e}")

        return features

    def analyze_corpus(
        self,
        image_dir: Path,
        output_path: Path,
        max_images: int = None,
    ) -> List[VisualFeatures]:
        """Analyze all images in a directory."""
        image_dir = Path(image_dir)

        # Find all images
        extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        image_paths = [
            p for p in image_dir.rglob("*")
            if p.suffix.lower() in extensions
        ]

        if max_images:
            image_paths = image_paths[:max_images]

        print(f"Found {len(image_paths)} images to analyze")

        # Analyze each
        results = []
        for path in tqdm(image_paths, desc="Analyzing"):
            try:
                features = self.analyze(str(path))
                results.append(features)
            except Exception as e:
                print(f"Failed: {path.name}: {e}")

        # Save results
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in results], f, indent=2)

        print(f"Saved {len(results)} results to {output_path}")
        return results


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Visual Analysis Pipeline")
    parser.add_argument("--image", type=str, help="Single image to analyze")
    parser.add_argument("--dir", type=str, help="Directory of images to analyze")
    parser.add_argument("--output", type=str, default="visual_features.json",
                        help="Output file path")
    parser.add_argument("--max", type=int, help="Maximum images to analyze")
    parser.add_argument("--model", choices=["florence", "clip", "both"],
                        default="both", help="Which models to use")
    parser.add_argument("--device", choices=["cuda", "cpu"], help="Device to use")

    args = parser.parse_args()

    use_florence = args.model in ["florence", "both"]
    use_clip = args.model in ["clip", "both"]

    pipeline = VisualPipeline(
        use_florence=use_florence,
        use_clip=use_clip,
        device=args.device,
    )

    if args.image:
        features = pipeline.analyze(args.image)
        print(json.dumps(features.to_dict(), indent=2))

    elif args.dir:
        pipeline.analyze_corpus(
            Path(args.dir),
            Path(args.output),
            max_images=args.max,
        )
    else:
        print("Usage:")
        print("  python -m rolebox_visual.vision_models --image path/to/image.png")
        print("  python -m rolebox_visual.vision_models --dir path/to/images/ --output results.json")


if __name__ == "__main__":
    main()
