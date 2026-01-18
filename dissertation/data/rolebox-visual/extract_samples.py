#!/usr/bin/env python
"""Extract sample screenshots from zip for testing"""

import zipfile
from pathlib import Path
import random
import sys

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Paths
zip_path = Path(__file__).parent / "data" / "raw" / "eit_screenshots.zip"
output_dir = Path(__file__).parent / "data" / "samples"

# Create output directory
output_dir.mkdir(parents=True, exist_ok=True)

print(f"Extracting samples from: {zip_path}")
print(f"Output directory: {output_dir}")

# Open zip and extract samples
with zipfile.ZipFile(zip_path, 'r') as zf:
    # Get all PNG files (not directories)
    all_files = [f for f in zf.namelist() if f.endswith('.png')]
    print(f"Total PNG files in zip: {len(all_files)}")

    # Group by KIC folder
    kic_files = {}
    for f in all_files:
        parts = f.split('/')
        if len(parts) >= 2:
            kic = parts[0]
            if kic not in kic_files:
                kic_files[kic] = []
            kic_files[kic].append(f)

    print(f"\nFiles by KIC:")
    for kic, files in sorted(kic_files.items()):
        print(f"  {kic}: {len(files)} files")

    # Extract 3 samples from each KIC (or all if less than 3)
    samples_per_kic = 3
    extracted = 0

    for kic, files in kic_files.items():
        # Create KIC subdirectory
        kic_dir = output_dir / kic
        kic_dir.mkdir(exist_ok=True)

        # Select random samples
        sample_files = random.sample(files, min(samples_per_kic, len(files)))

        for f in sample_files:
            # Extract file
            filename = Path(f).name
            target_path = kic_dir / filename

            with zf.open(f) as src:
                with open(target_path, 'wb') as dst:
                    dst.write(src.read())

            extracted += 1
            print(f"  Extracted: {kic}/{filename}")

print(f"\nTotal extracted: {extracted} files")
print(f"Output: {output_dir}")
