from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT
PORT = int(os.environ.get("CET4_PLAYER_PORT", "8000"))
HOST = os.environ.get("CET4_PLAYER_HOST", "127.0.0.1")
LOG = PROJECT_ROOT / "server.log"


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stdout.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format % args))
        sys.stdout.flush()


def main():
    os.chdir(ROOT)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    log = LOG.open("a", encoding="utf-8", buffering=1)
    sys.stdout = log
    sys.stderr = log
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving {ROOT} at http://{HOST}:{PORT}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
