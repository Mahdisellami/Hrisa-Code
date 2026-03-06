#!/usr/bin/env python3
"""Quick validation script for Web UI functionality."""

import sys
from pathlib import Path


def test_imports():
    """Test that all web UI modules can be imported."""
    print("Testing imports...")

    try:
        from hrisa_code.web import WebAgentManager, AgentStatus, AgentInfo
        print("  ✓ WebAgentManager imports successfully")
    except ImportError as e:
        print(f"  ✗ Failed to import WebAgentManager: {e}")
        return False

    try:
        from hrisa_code.web import app, run_server
        print("  ✓ FastAPI app imports successfully")
    except ImportError as e:
        print(f"  ✗ Failed to import FastAPI app: {e}")
        print("  → Install web dependencies: pip install -e '.[web]'")
        return False

    return True


def test_static_files():
    """Test that static files exist."""
    print("\nTesting static files...")

    static_dir = Path("src/hrisa_code/web/static")

    files = ["index.html", "styles.css", "app.js"]
    all_exist = True

    for file in files:
        file_path = static_dir / file
        if file_path.exists():
            print(f"  ✓ {file} exists")
        else:
            print(f"  ✗ {file} missing")
            all_exist = False

    return all_exist


def test_ollama():
    """Test Ollama connection."""
    print("\nTesting Ollama connection...")

    import subprocess

    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            models = [
                line.split()[0]
                for line in result.stdout.strip().split("\n")[1:]
                if line.strip()
            ]
            print(f"  ✓ Ollama is running with {len(models)} model(s)")
            if models:
                print(f"    Available: {', '.join(models[:3])}")
            return True
        else:
            print("  ✗ Ollama not responding")
            print("  → Start Ollama: ollama serve")
            return False

    except FileNotFoundError:
        print("  ✗ Ollama not installed")
        print("  → Install from: https://ollama.ai/")
        return False
    except subprocess.TimeoutExpired:
        print("  ✗ Ollama connection timeout")
        return False


def test_dependencies():
    """Test required dependencies."""
    print("\nTesting dependencies...")

    deps = {
        "fastapi": "FastAPI web framework",
        "uvicorn": "ASGI server",
        "websockets": "WebSocket support",
    }

    all_installed = True

    for dep, description in deps.items():
        try:
            __import__(dep)
            print(f"  ✓ {dep} installed ({description})")
        except ImportError:
            print(f"  ✗ {dep} missing ({description})")
            all_installed = False

    if not all_installed:
        print("\n  → Install with: pip install -e '.[web]'")

    return all_installed


def main():
    """Run all tests."""
    print("=" * 60)
    print("Hrisa Code Web UI - Quick Validation")
    print("=" * 60)

    results = {
        "Imports": test_imports(),
        "Static Files": test_static_files(),
        "Dependencies": test_dependencies(),
        "Ollama": test_ollama(),
    }

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All tests passed! Ready to start the web UI.")
        print("\nTo start the server:")
        print("  hrisa web")
        print("\nThen open: http://localhost:8000")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
