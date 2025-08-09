#!/usr/bin/env python3
"""
Start script for trendSaaS application (single-port)
Runs the unified FastAPI app that serves both API and static frontend.
"""

import subprocess
import sys
import os
import time


def main():
    print("Starting TrendSaaS unified application...")
    port = os.getenv("PORT", "3000")
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Server will run on http://{host}:{port}")
    print("Press Ctrl+C to stop")
    print("-" * 50)

    process = None
    try:
        # Run the unified app which serves both API and static frontend
        process = subprocess.Popen([sys.executable, "main_new.py"])
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("✓ Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=3)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

if __name__ == "__main__":
    main()