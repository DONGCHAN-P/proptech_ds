"""Serve only the prepared web directory on localhost. Ctrl+C stops it."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
import argparse,threading,webbrowser
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--open-browser',action='store_true');args=p.parse_args()
root=Path(__file__).resolve().parent/'web'
server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(SimpleHTTPRequestHandler,directory=str(root)))
print(f'Atlas: http://127.0.0.1:{args.port}/',flush=True)
if args.open_browser:threading.Timer(.5,lambda:webbrowser.open(f'http://127.0.0.1:{args.port}/')).start()
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
