#!/usr/bin/env python3
"""
Testara Device Server — runs on your Mac alongside Appium.
Exposes GET /devices returning available iOS simulators from xcrun simctl.

Usage:
    python3 device_server.py          # listens on 0.0.0.0:4724
    python3 device_server.py --port 4724
"""
import argparse
import asyncio
import json
import logging
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("device-server")


def get_simulators() -> list[dict]:
    """Run xcrun simctl and return available simulators."""
    import subprocess

    result = subprocess.run(
        ["xcrun", "simctl", "list", "devices", "available", "--json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error("xcrun failed: %s", result.stderr)
        return []

    data = json.loads(result.stdout)
    devices = []

    for runtime_key, device_list in data.get("devices", {}).items():
        # runtime_key looks like "com.apple.CoreSimulator.SimRuntime.iOS-17-0"
        match = re.search(r"iOS-(\d+)-(\d+)", runtime_key)
        if not match:
            continue
        major, minor = match.group(1), match.group(2)
        ios_version = f"{major}.{minor}" if minor != "0" else major

        for d in device_list:
            if not d.get("isAvailable", False):
                continue
            devices.append(
                {
                    "name": d["name"],
                    "udid": d["udid"],
                    "os_version": ios_version,
                    "os": f"iOS {ios_version}",
                    "state": d.get("state", "Shutdown"),
                }
            )

    # Sort: booted first, then by iOS version desc, then name
    devices.sort(key=lambda x: (x["state"] != "Booted", [-int(p) for p in x["os_version"].split(".")], x["name"]))
    return devices


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info(fmt, *args)

    def _json(self, status: int, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path in ("/devices", "/devices/"):
            try:
                devices = get_simulators()
                self._json(200, {"devices": devices, "total": len(devices)})
            except Exception as e:
                log.exception("Error listing simulators")
                self._json(500, {"error": str(e)})
        elif self.path in ("/health", "/"):
            self._json(200, {"status": "ok", "service": "testara-device-server"})
        else:
            self._json(404, {"error": "Not found"})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()


def main():
    parser = argparse.ArgumentParser(description="Testara Device Server")
    parser.add_argument("--port", type=int, default=4724, help="Port to listen on (default: 4724)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), Handler)
    log.info("Testara Device Server listening on %s:%d", args.host, args.port)
    log.info("Endpoints: GET /devices  GET /health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down.")


if __name__ == "__main__":
    main()
