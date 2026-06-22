"""
tests/validate_environment.py — Toolchain & environment validation (Hard Stop 3).

De-risks the stack BEFORE collecting evidence: confirms the Python runtime, every
required package (with installed version), environment configuration, the local LLM
runtime, and the repository layout. Designed to be run repeatedly and produce the same
report from a clean restart.

Run from the repository root:
    python tests/validate_environment.py

Legend:  [PASS] ok   [WARN] non-blocking (e.g. optional runtime/key absent)   [FAIL] blocking
"""

import importlib
import os
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_PACKAGES = [
    "yfinance", "pandas", "numpy", "pytz", "requests",
    "transformers", "torch", "ollama", "pytest",
]

REPO_PATHS = [
    "services/data_ingestion", "services/sentiment_analysis",
    "agents/strategy_agent", "agents/signal_filter.py", "agents/risk_validator.py",
    "core/scheduler.py", "pipeline.py", "main.py",
    "requirements.txt", ".env.example", "tests/smoke_test.py",
]

passes = warns = fails = 0


def ok(msg):
    global passes; passes += 1; print(f"  [PASS] {msg}")


def warn(msg):
    global warns; warns += 1; print(f"  [WARN] {msg}")


def fail(msg):
    global fails; fails += 1; print(f"  [FAIL] {msg}")


def check_python():
    print("\n[1] Python runtime")
    v = sys.version_info
    label = f"Python {v.major}.{v.minor}.{v.micro}"
    (ok if (v.major, v.minor) >= (3, 11) else fail)(f"{label} (require 3.11+)")


def check_packages():
    print("\n[2] Required packages (with installed version)")
    for name in REQUIRED_PACKAGES:
        try:
            mod = importlib.import_module(name)
            ver = getattr(mod, "__version__", "unknown")
            ok(f"{name:<13} {ver}")
        except Exception as exc:  # noqa: BLE001
            fail(f"{name:<13} import failed: {type(exc).__name__}")


def check_env():
    print("\n[3] Environment configuration")
    env_path = os.path.join(REPO_ROOT, ".env")
    if os.path.exists(env_path):
        ok(".env file present")
    else:
        warn(".env not found — copy .env.example and fill in keys before live runs")
    if os.environ.get("BRAVE_API_KEY"):
        ok("BRAVE_API_KEY is set")
    else:
        warn("BRAVE_API_KEY not set — sentiment news fetch will be unavailable")


def check_ollama():
    print("\n[4] Local LLM runtime (Ollama / llama3.2)")
    try:
        import ollama
        models = ollama.list().get("models", [])
        names = [m.get("model", m.get("name", "")) for m in models]
        if any("llama3.2" in n for n in names):
            ok("Ollama reachable; llama3.2 present")
        elif names:
            warn(f"Ollama reachable but llama3.2 not pulled (have: {', '.join(names)[:60]})")
        else:
            warn("Ollama reachable but no models pulled — run: ollama pull llama3.2")
    except Exception as exc:  # noqa: BLE001
        warn(f"Ollama not reachable ({type(exc).__name__}) — start it with: ollama serve")


def check_repo_layout():
    print("\n[5] Repository layout")
    for rel in REPO_PATHS:
        (ok if os.path.exists(os.path.join(REPO_ROOT, rel)) else fail)(rel)


def main():
    print("=" * 64)
    print(" ENVIRONMENT & TOOLCHAIN VALIDATION — Hard Stop 3")
    print(f" Run at: {datetime.now().isoformat(timespec='seconds')}")
    print(f" Repo:   {REPO_ROOT}")
    print("=" * 64)

    check_python()
    check_packages()
    check_env()
    check_ollama()
    check_repo_layout()

    print("\n" + "-" * 64)
    print(f" SUMMARY: {passes} pass, {warns} warn, {fails} fail")
    if fails == 0:
        print(" ENVIRONMENT OK — toolchain validated (warnings are non-blocking).")
    else:
        print(" ENVIRONMENT NOT READY — resolve [FAIL] items above.")
    print("=" * 64)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
