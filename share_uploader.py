# Instant WebGIS Viewer — QGIS Plugin
# share_uploader.py — publishes the exported HTML to various hosts or serves locally
# Copyright (C) 2026 Ballu Harish  |  GPL v2 or later

import ssl
import json
import time
import base64
import urllib.request
import urllib.error
import http.server
import socketserver
import socket
import threading
import os

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) InstantWebGISViewer'


def _ignore(e):
    pass


def _ctx():
    try:
        return ssl.create_default_context()
    except Exception as e:
        _ignore(e)
        return None


def _gh(method, url, token, payload=None, timeout=60):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', 'Bearer ' + token)
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('User-Agent', UA)
    req.add_header('X-GitHub-Api-Version', '2022-11-28')
    if data is not None:
        req.add_header('Content-Type', 'application/json')
    # Audit URL scheme B310
    if not isinstance(url, str) or not (url.startswith('http://') or url.startswith('https://')):
        raise ValueError('Only HTTP(S) protocol is allowed')
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as r:  # nosec B310
            body = r.read().decode('utf-8', 'replace')
            return getattr(r, 'status', 200), (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')
        try:
            j = json.loads(body)
        except Exception as ex:
            _ignore(ex)
            j = {'message': body[:300]}
        return e.code, j


def upload_github(html_path, token, owner=None, repo='iwv-maps', branch='main'):
    """Publish the HTML to a PUBLIC GitHub repo; return a statically render URL."""
    token = (token or '').strip()
    if not token:
        raise RuntimeError('No GitHub token provided.')

    # 1) resolve owner from the token if not given
    if not owner:
        st, j = _gh('GET', 'https://api.github.com/user', token)
        if st != 200 or 'login' not in j:
            raise RuntimeError('Bad token or GitHub unreachable: '
                               + str(j.get('message', st)))
        owner = j['login']

    # 2) ensure a public repo exists
    st, j = _gh('GET', 'https://api.github.com/repos/%s/%s' % (owner, repo), token)
    if st == 404:
        st2, j2 = _gh('POST', 'https://api.github.com/user/repos', token,
                      {'name': repo, 'private': False, 'auto_init': True,
                       'description': 'Maps shared from Instant WebGIS Viewer'})
        if st2 not in (201, 202):
            raise RuntimeError('Could not create repo "%s": %s'
                               % (repo, j2.get('message', st2)))
        time.sleep(2)
    elif st == 200:
        if j.get('private'):
            raise RuntimeError('Repo "%s" is PRIVATE — the share link will not '
                               'open. Make it public or use a different name.' % repo)
        branch = j.get('default_branch', branch) or branch
    else:
        raise RuntimeError('GitHub repo check failed: ' + str(j.get('message', st)))

    # 3) upload with a unique filename
    with open(html_path, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode('ascii')
    ts = time.strftime('%Y%m%d-%H%M%S')
    path = 'maps/map-%s.html' % ts
    st, j = _gh('PUT',
                'https://api.github.com/repos/%s/%s/contents/%s' % (owner, repo, path),
                token, {'message': 'Add map ' + ts,
                        'content': content_b64, 'branch': branch})
    if st not in (200, 201):
        raise RuntimeError('Upload to GitHub failed: ' + str(j.get('message', st)))

    url = 'https://raw.githack.com/%s/%s/%s/%s' % (owner, repo, branch, path)
    return {'url': url, 'host': 'GitHub (%s/%s)' % (owner, repo),
            'expiry': 'Stays until you delete it in your repo', 'permanent': True}


# ── MULTIPART Uploader Helper ────────────────────────────────────────────────
def _upload_multipart(url, fields, files, timeout=30):
    import uuid
    boundary = f'----WebKitFormBoundary{uuid.uuid4().hex[:16]}'
    body = []
    for k, v in fields.items():
        body.append(f'--{boundary}'.encode('utf-8'))
        body.append(f'Content-Disposition: form-data; name="{k}"'.encode('utf-8'))
        body.append(b'')
        body.append(str(v).encode('utf-8'))
    for k, (filename, content, mimetype) in files.items():
        body.append(f'--{boundary}'.encode('utf-8'))
        body.append(f'Content-Disposition: form-data; name="{k}"; filename="{filename}"'.encode('utf-8'))
        body.append(f'Content-Type: {mimetype}'.encode('utf-8'))
        body.append(b'')
        body.append(content)
    body.append(f'--{boundary}--'.encode('utf-8'))
    body.append(b'')
    payload = b'\r\n'.join(body)

    req = urllib.request.Request(url, data=payload, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req.add_header('User-Agent', UA)
    
    # Audit URL scheme B310
    if not isinstance(url, str) or not (url.startswith('http://') or url.startswith('https://')):
        raise ValueError('Only HTTP(S) protocol is allowed')
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as response:  # nosec B310
        return response.read().decode('utf-8', 'replace')


# ── Uguu.se Uploader (Large Files Fallback) ──────────────────────────────────
def upload_uguu(html_path):
    """Upload large HTML maps to uguu.se (supports up to 100MB, direct rendering)."""
    with open(html_path, 'rb') as f:
        content = f.read()
    files = {'files[]': ('map.html', content, 'text/html')}
    res = _upload_multipart('https://uguu.se/upload', {}, files, timeout=60)
    data = json.loads(res)
    url = data.get('files', [{}])[0].get('url', '')
    if url.startswith('http'):
        return {'url': url, 'host': 'uguu.se (Large File Host)', 'expiry': 'Expires in 3 hours'}
    raise RuntimeError('uguu.se response invalid: ' + res[:100])


# ── pagedrop.io Upload ───────────────────────────────────────────────────────
def upload_pagedrop(html_path):
    """Upload HTML map to pagedrop.io (reliable, direct rendering, no token)."""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Payload for pagedrop.io
    payload = {
        'html': html_content,
        'ttl': '3d'  # Page expires in 3 days
    }
    data = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request('https://pagedrop.io/api/upload', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', UA)

    # Audit URL scheme B310
    url_str = req.full_url
    if not isinstance(url_str, str) or not (url_str.startswith('http://') or url_str.startswith('https://')):
        raise ValueError('Only HTTP(S) protocol is allowed')
    try:
        with urllib.request.urlopen(req, timeout=45, context=_ctx()) as r:  # nosec B310
            body = r.read().decode('utf-8', 'replace')
            res_data = json.loads(body)
            url = res_data.get('data', {}).get('url') or res_data.get('url')
            if url:
                return {'url': url, 'host': 'pagedrop.io', 'expiry': 'Expires in 3 days'}
            raise RuntimeError('Pagedrop response missing URL: ' + body[:100])
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')
        raise RuntimeError(f'Pagedrop upload failed with code {e.code}: {body[:200]}')


def upload_public(html_path):
    """Try pagedrop.io first, fall back to uguu.se if too large or blocked."""
    errors = []
    try:
        return upload_pagedrop(html_path)
    except Exception as e:
        errors.append(f"Pagedrop failed: {e}")

    try:
        return upload_uguu(html_path)
    except Exception as e:
        errors.append(f"Uguu.se failed: {e}")

    raise RuntimeError("Public sharing failed:\n" + "\n".join(errors))


# ── Local WiFi/LAN Server ────────────────────────────────────────────────────
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


class LocalMapServer:
    _server_instance = None
    _server_thread = None
    _current_file = None

    @classmethod
    def start_serving(cls, html_path):
        cls.stop_serving()
        cls._current_file = html_path
        ip = get_local_ip()
        
        # Find a free port
        port = 8080
        for p in range(8080, 8120):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind((ip, p))
                s.close()
                port = p
                break
            except Exception as e:
                _ignore(e)
                continue

        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass
                
            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
                self.end_headers()

            def do_GET(self):
                if self.path == '/api/get_token':
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    try:
                        from qgis.core import QgsSettings
                        s = QgsSettings()
                        token = s.value('InstantWebGISViewer/github_token', '', type=str)
                        self.wfile.write(json.dumps({'token': token}).encode('utf-8'))
                    except Exception as e:
                        self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                elif self.path in ('/', '/' + os.path.basename(html_path)):
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    try:
                        with open(html_path, 'rb') as f:
                            content = f.read()
                        self.send_header("Content-Length", str(len(content)))
                        self.end_headers()
                        self.wfile.write(content)
                    except Exception as e:
                        self.wfile.write(str(e).encode())
                else:
                    self.send_error(404, "File not found")

            def do_POST(self):
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                
                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                except Exception as e:
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Read error: ' + str(e)}).encode('utf-8'))
                    return

                if self.path == '/api/upload_public':
                    try:
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
                            tmp.write(post_data)
                            tmp_path = tmp.name
                        try:
                            res = upload_public(tmp_path)
                            self.end_headers()
                            self.wfile.write(json.dumps(res).encode('utf-8'))
                        finally:
                            try:
                                os.remove(tmp_path)
                            except Exception as ex:
                                _ignore(ex)
                    except Exception as e:
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                        
                elif self.path == '/api/upload_github':
                    try:
                        body_data = json.loads(post_data.decode('utf-8'))
                        token = body_data.get('token')
                        html_str = body_data.get('html')
                        
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tmp:
                            tmp.write(html_str)
                            tmp_path = tmp.name
                        try:
                            res = upload_github(tmp_path, token)
                            try:
                                from qgis.core import QgsSettings
                                s = QgsSettings()
                                s.setValue('InstantWebGISViewer/github_token', token)
                            except Exception as ex:
                                _ignore(ex)
                            self.end_headers()
                            self.wfile.write(json.dumps(res).encode('utf-8'))
                        finally:
                            try:
                                os.remove(tmp_path)
                            except Exception as ex:
                                _ignore(ex)
                    except Exception as e:
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.end_headers()

        server = socketserver.TCPServer((ip, port), Handler)
        cls._server_instance = server
        
        def serve():
            try:
                server.serve_forever()
            except Exception as ex:
                _ignore(ex)
                
        cls._server_thread = threading.Thread(target=serve, daemon=True)
        cls._server_thread.start()
        
        url = f"http://{ip}:{port}/{os.path.basename(html_path)}"
        return url

    @classmethod
    def stop_serving(cls):
        if cls._server_instance:
            try:
                cls._server_instance.shutdown()
                cls._server_instance.server_close()
            except Exception as ex:
                _ignore(ex)
            cls._server_instance = None
            cls._server_thread = None
