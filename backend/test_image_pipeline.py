#!/usr/bin/env python3
"""
Test image-to-LaTeX pipeline with sample images.
"""
import asyncio
import base64
import os
import sys

sys.path.insert(0, '.')

from input.parser import InputParser

def encode_image_to_base64(image_path: str) -> str:
    """Read image file and return base64 data URL."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    b64 = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:image/png;base64,{b64}"

async def test_image(image_path: str):
    parser = InputParser()
    b64 = encode_image_to_base64(image_path)
    try:
        latex = await parser.image_to_latex(b64)
        print(f"Image: {os.path.basename(image_path)}")
        print(f"  LaTeX: {latex}")
        print()
        return latex
    except Exception as e:
        print(f"Image: {os.path.basename(image_path)}")
        print(f"  ERROR: {e}")
        print()
        return None

async def main():
    sample_dir = "../test/sample-image-problems"
    if not os.path.exists(sample_dir):
        sample_dir = "test/sample-image-problems"
    if not os.path.exists(sample_dir):
        print(f"Sample directory not found: {sample_dir}")
        return
    
    files = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not files:
        print("No image files found.")
        return
    
    print(f"Testing {len(files)} images...")
    for f in files[:3]:  # limit to 3 for speed
        path = os.path.join(sample_dir, f)
        await test_image(path)

if __name__ == "__main__":
    asyncio.run(main())