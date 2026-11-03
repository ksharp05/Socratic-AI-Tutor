from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path


def serve(tutor,port=8766):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass  # Do not log learner messages or session IDs.
        def send(self,status,data,kind='application/json; charset=utf-8'):
            body=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode('utf-8')
            self.send_response(status); self.send_header('Content-Type',kind)
            self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
            self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
        def host_ok(self):
            return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
        def do_GET(self):
            if not self.host_ok(): self.send(403,{'error':'Local host only'}); return
            if self.path=='/': self.send(200,Path(__file__).with_name('preview.html').read_bytes(),'text/html; charset=utf-8')
            elif self.path=='/api/scopes': self.send(200,tutor.retriever.scopes())
            else: self.send(404,{'error':'Not found'})
        def do_POST(self):
            if not self.host_ok() or self.headers.get('Origin',f'http://{self.headers.get("Host")}')!=f'http://{self.headers.get("Host")}':
                self.send(403,{'error':'Same-origin local requests only'}); return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=16384 or self.headers.get_content_type()!='application/json': raise ValueError('Expected a small JSON request')
                data=json.loads(self.rfile.read(size))
                if not isinstance(data,dict): raise ValueError('Expected object')
                if self.path=='/api/session':
                    allowed={'grade','subject','book','unit_file_index','mode'}
                    if not set(data)<=allowed: raise ValueError('Unknown session field')
                    self.send(200,{'session_id':tutor.new_session(**data),'live':tutor.provider is not None})
                elif self.path=='/api/turn':
                    self.send(200,tutor.turn(data['session_id'],data['text']))
                elif self.path=='/api/reset':
                    tutor.reset(data['session_id']); self.send(200,{'deleted':True})
                else: self.send(404,{'error':'Not found'})
            except (ValueError,KeyError,TypeError): self.send(400,{'error':'Invalid request or session. Check the class, subject and message.'})
            except Exception: self.send(500,{'error':'The local preview could not complete this turn.'})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'Local development preview: http://127.0.0.1:{port} (Ctrl+C to stop)',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
