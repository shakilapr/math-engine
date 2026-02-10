import sys
import importlib

required = [
    "fastapi", "uvicorn", "numpy", "scipy", "sympy", "matplotlib", 
    "mpmath", "PIL", "pix2tex", "fitz", "pdfplumber"
]

missing = []
for package in required:
    try:
        importlib.import_module(package)
        print(f"✅ {package}")
    except ImportError:
        missing.append(package)
        print(f"❌ {package}")

if missing:
    print(f"\nMissing packages: {', '.join(missing)}")
    sys.exit(1)

print("\nAll backend dependencies are installed! 🚀")
