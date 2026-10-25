"""Export the current 320 × 240 browser previews with Chrome or Chromium."""

import argparse
import base64
from functools import partial
import html
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import threading


HERE = Path(__file__).resolve().parent


def find_browser(explicit):
    candidates = [explicit] if explicit else [
        "google-chrome", "chromium", "chromium-browser", "chrome", "msedge",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        *[str(Path(os.environ.get(root, "")) / app) for root in
          ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA") for app in
          ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe")],
    ]
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    raise ValueError("Chrome or Chromium was not found. Pass --browser /path/to/browser.")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def export(browser, output, alternatives):
    handler = partial(QuietHandler, directory=str(HERE.parent))
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            url = f"http://127.0.0.1:{port}/fresh/export.html"
            if alternatives:
                url += "?alternatives=1"
            with tempfile.TemporaryDirectory(prefix="walking-export-") as profile:
                result = subprocess.run([
                    browser, "--headless=new", "--disable-gpu", "--no-first-run",
                    f"--user-data-dir={profile}", "--virtual-time-budget=10000",
                    "--dump-dom", url,
                ], capture_output=True, text=True, check=True, timeout=60)
        finally:
            server.shutdown()
            thread.join()
    match = re.search(r'<pre id="out"[^>]*>(.*?)</pre>', result.stdout, re.S)
    lines = html.unescape(match[1]).strip().splitlines() if match else []
    expected = 20 if alternatives else 8
    if len(lines) != expected:
        raise ValueError("Preview export failed. Check your network connection for Mona Sans. "
                         + " ".join(lines)[:300])
    images = []
    for line in lines:
        name, url = line.split(" ", 1)
        target = output / f"{name}.png"
        if not target.resolve().is_relative_to(output.resolve()):
            raise ValueError(f"Invalid export filename: {name}")
        if not url.startswith("data:image/png;base64,"):
            raise ValueError(f"Invalid PNG data for {name}")
        data = base64.b64decode(url.split(",", 1)[1], validate=True)
        if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 24 or struct.unpack(">II", data[16:24]) != (320, 240):
            raise ValueError(f"Expected a 320 × 240 PNG for {name}")
        images.append((target, data))
    for target, data in images:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"saved {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Chrome, Chromium or Edge executable")
    parser.add_argument("--output", type=Path, default=HERE, help="PNG folder (default: final/)")
    parser.add_argument("--alternatives", action="store_true", help="also export the 12 comparison variants")
    args = parser.parse_args()
    try:
        export(find_browser(args.browser), args.output, args.alternatives)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Export failed: {error}\n")


if __name__ == "__main__":
    main()
