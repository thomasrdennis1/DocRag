#!/usr/bin/env python3
"""
Document RAG Search — Streamlit Launcher
=========================================
Launches the Streamlit app with sensible defaults.

USAGE:
    python run.py                 # default port 5001
    python run.py --port 8501     # custom port
"""

import sys
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(description="Launch DocRAG Search (Streamlit)")
    parser.add_argument("--port", default=5001, type=int, help="Port (default: 5001)")
    args = parser.parse_args()

    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(args.port),
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false",
    ]

    print(f"\nStarting DocRAG Search on http://localhost:{args.port}")
    print("Press Ctrl+C to stop.\n")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
