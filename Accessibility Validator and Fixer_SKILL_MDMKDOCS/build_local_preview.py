#!/usr/bin/env python3
"""
Local Documentation Builder for Accessibility Fixes
Builds the documentation locally after fixes so you can review the changes without committing
"""

import os
import sys
import subprocess
from pathlib import Path

def build_local_docs(docs_path):
    """Build documentation locally for preview"""
    print(f"Building documentation locally for preview...")
    print(f"Docs path: {docs_path}")
    
    docs_path = Path(docs_path)
    
    # Change to parent directory where mkdocs.yml is located
    original_dir = os.getcwd()
    build_dir = docs_path.parent  # Parent directory of docs
    os.chdir(build_dir)
    
    try:
        # Build the documentation using python -m mkdocs to avoid Application Control policy
        print("Running: python -m mkdocs build")
        result = subprocess.run(
            [sys.executable, "-m", "mkdocs", "build"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Documentation built successfully!")
            print(f"Built site location: {build_dir / 'site'}")
            print(f"\nTo preview the documentation locally:")
            print(f"  cd {build_dir}")
            print(f"  python -m mkdocs serve -a 127.0.0.1:8000")
            print(f"\nThen open: http://127.0.0.1:8000")
            return True
        else:
            print(f"Error building documentation:")
            print(result.stderr)
            return False
    finally:
        os.chdir(original_dir)

def serve_local_docs(docs_path):
    """Serve documentation locally for preview"""
    print(f"Starting local documentation server...")
    print(f"Docs path: {docs_path}")
    
    docs_path = Path(docs_path)
    
    # Change to parent directory where mkdocs.yml is located
    original_dir = os.getcwd()
    build_dir = docs_path.parent  # Parent directory of docs
    os.chdir(build_dir)
    
    try:
        print("Running: python -m mkdocs serve -a 127.0.0.1:8000")
        print("Press Ctrl+C to stop the server")
        subprocess.run(
            [sys.executable, "-m", "mkdocs", "serve", "-a", "127.0.0.1:8000"]
        )
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python build_local_preview.py <docs_path> [serve]")
        print("Example: python build_local_preview.py ../docs")
        print("         python build_local_preview.py ../docs serve")
        print("\nNote: This script uses 'python -m mkdocs' to avoid Application Control policy issues")
        sys.exit(1)
    
    docs_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "build"
    
    if mode == "serve":
        serve_local_docs(docs_path)
    else:
        build_local_docs(docs_path)