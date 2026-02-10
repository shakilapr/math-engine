#!/usr/bin/env python3
import sys
try:
    from pix2tex.cli import LatexOCR
    print("SUCCESS: LatexOCR imported")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Other error: {e}")
    sys.exit(2)