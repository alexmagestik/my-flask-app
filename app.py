"""Simple Flask demo application with health, info and math endpoints."""

import math
import os
import platform
import socket
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version

from flask import Flask, jsonify, request

app = Flask(__name__)
START_TIME = time.time()


def flask_version() -> str:
    try:
        return version("flask")
    except PackageNotFoundError:  # pragma: no cover - flask is always installed
        return "unknown"


def parse_number(raw: str, name: str) -> float:
    """Convert a URL path segment to a finite float or raise ValueError."""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"Parameter '{name}' must be a number, got '{raw}'") from None
    if not math.isfinite(value):
        raise ValueError(f"Parameter '{name}' must be a finite number")
    return value


def normalize(value: float):
    """Return an int when the result has no fractional part."""
    if value.is_integer() and abs(value) <= 2**53:
        return int(value)
    return value


@app.get("/")
def index():
    return jsonify(
        {
            "service": "my-flask-app",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "info": "/info",
                "multiply": "/multiply/<a>/<b>",
                "divide": "/divide/<a>/<b>",
            },
            "docs": "See README.md for usage",
        }
    )


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "uptime_seconds": round(time.time() - START_TIME, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )


@app.get("/info")
def info():
    return jsonify(
        {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor() or "unknown",
            "python_version": sys.version.split()[0],
            "flask_version": flask_version(),
            "pid": os.getpid(),
            "cpu_count": os.cpu_count(),
            "cwd": os.getcwd(),
            "server_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )


@app.get("/multiply/<a>/<b>")
def multiply(a: str, b: str):
    try:
        left = parse_number(a, "a")
        right = parse_number(b, "b")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "operation": "multiply",
            "a": normalize(left),
            "b": normalize(right),
            "result": normalize(left * right),
        }
    )


@app.get("/divide/<a>/<b>")
def divide(a: str, b: str):
    try:
        left = parse_number(a, "a")
        right = parse_number(b, "b")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if right == 0:
        return jsonify({"error": "Division by zero is not allowed"}), 400

    return jsonify(
        {
            "operation": "divide",
            "a": normalize(left),
            "b": normalize(right),
            "result": normalize(left / right),
        }
    )


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({"error": "Not found", "path": request.path}),
        404,
    )


@app.errorhandler(405)
def method_not_allowed(error):
    return (
        jsonify({"error": "Method not allowed", "method": request.method, "path": request.path}),
        405,
    )


if __name__ == "__main__":
    # Local development only; Docker runs the app through gunicorn.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
