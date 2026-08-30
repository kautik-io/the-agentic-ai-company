#!/usr/bin/env python3
"""Minimal GitHub webhook → pull + auto deploy."""

import argparse
import hashlib
import hmac
import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


def run_deploy(root: str) -> None:
    subprocess.run(
        [f"{root}/scripts/github-sync.sh", "sync"],
        cwd=root,
        check=False,
    )


class WebhookHandler(BaseHTTPRequestHandler):
    secret: str = ""
    root: str = ""

    def log_message(self, fmt, *args):
        print(f"[webhook] {self.address_string()} - {fmt % args}")

    def do_POST(self):
        if self.path not in ("/webhook", "/"):
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if self.secret:
            sig = self.headers.get("X-Hub-Signature-256", "")
            expected = "sha256=" + hmac.new(
                self.secret.encode(), body, hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(sig, expected):
                self.send_error(401, "Invalid signature")
                return

        event = self.headers.get("X-GitHub-Event", "")
        if event == "ping":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"pong")
            return

        if event == "push":
            payload = json.loads(body.decode())
            ref = payload.get("ref", "")
            print(f"[webhook] push to {ref}")
            run_deploy(self.root)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"deploy triggered")
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ignored")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--secret", default="")
    parser.add_argument("--root", required=True)
    args = parser.parse_args()

    WebhookHandler.secret = args.secret
    WebhookHandler.root = args.root

    server = HTTPServer(("0.0.0.0", args.port), WebhookHandler)
    print(f"[webhook] listening on 0.0.0.0:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
