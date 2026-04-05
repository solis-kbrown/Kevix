#!/usr/bin/env python3
"""
ServerRoot.net Dashboard Server
Serves static files + proxies /api/* to Flask on :5001
Runs on port 3003
"""
import http.server
import urllib.request
import urllib.error
import json
import os
import sys

FLASK_API = "http://localhost:5001"
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def log_message(self, format, *args):
        pass  # suppress access logs

    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_to_flask()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_to_flask()
        else:
            self.send_error(405)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def proxy_to_flask(self):
        url = FLASK_API + self.path
        try:
            # Read body if POST
            body = None
            if self.command == 'POST':
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length) if length else None

            req = urllib.request.Request(url, data=body, method=self.command)
            req.add_header('Content-Type', self.headers.get('Content-Type', 'application/json'))

            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_cors_headers()
                self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
                self.send_header('Content-Length', len(data))
                self.end_headers()
                self.wfile.write(data)

        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(data))
            self.end_headers()
            self.wfile.write(data)
        except Exception as ex:
            err = json.dumps({'error': str(ex)}).encode()
            self.send_response(502)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(err))
            self.end_headers()
            self.wfile.write(err)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3003
    server = http.server.ThreadingHTTPServer(('0.0.0.0', port), DashboardHandler)
    print(f"[Dashboard] Serving on port {port} | Proxying /api/* -> {FLASK_API}")
    server.serve_forever()