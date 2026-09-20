#!/usr/bin/env python3
"""
K.Z. Pendrake — Admin Server  (port 8080)
Single-author admin panel: edits data.js / synopsis / books / news / images
for this site only, plus a "Build" action that regenerates dist/ via
scripts/build.py.

Usage:  python admin_server.py
Panel:  http://localhost:8080/admin
"""
from flask import Flask, request, jsonify, send_from_directory, abort
import os, json, re, subprocess, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))
from image_optimize import optimize_to_webp
from werkzeug.utils import secure_filename

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

LANGS    = ['bg', 'en', 'de', 'fr', 'it', 'nl', 'es', 'pt', 'se']
IMG_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}


def apath(*parts):
    return os.path.join(BASE, *parts)


def js_to_json(text, varname='authorData'):
    """Parse data.js (JS object literal) into a Python dict.

    Fast path: files written by write_data_js() are already valid JSON.
    Slow path: hand-written JS — string literals are protected as
    placeholders before any other transform, so comment stripping /
    key-quoting can't mangle URLs or text content.
    """
    m = re.search(r'const\s+' + re.escape(varname) + r'\s*=\s*(\{.*\})\s*;?\s*$', text, re.DOTALL)
    if not m:
        raise ValueError(f'Cannot locate {varname} object in data.js')
    obj = m.group(1)

    try:
        return json.loads(obj)
    except json.JSONDecodeError:
        pass

    strings = []

    def save_template(match):
        content = match.group(1)
        content = content.replace('\\', '\\\\').replace('"', '\\"')
        content = content.replace('\r\n', '\\n').replace('\n', '\\n') \
                         .replace('\r', '').replace('\t', '\\t')
        strings.append(f'"{content}"')
        return f'\x02{len(strings)-1}\x02'
    obj = re.sub(r'`([^`]*)`', save_template, obj, flags=re.DOTALL)

    def save_str(match):
        strings.append(match.group(0))
        return f'\x02{len(strings)-1}\x02'
    obj = re.sub(r'"(?:[^"\\]|\\.)*"', save_str, obj)

    obj = re.sub(r'//[^\n]*', '', obj)
    obj = re.sub(r'(?<!["\w\x02])([a-zA-Z_$][a-zA-Z0-9_$]*)(\s*):', r'"\1"\2:', obj)
    obj = re.sub(r',(\s*[}\]])', r'\1', obj)

    for i, s_val in enumerate(strings):
        obj = obj.replace(f'\x02{i}\x02', s_val)

    return json.loads(obj)


def write_data_js(data):
    path = apath('data.js')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('const authorData = ')
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write(';\n')


# ── Admin UI static files ─────────────────────────────────────────────────

@app.route('/admin', strict_slashes=False)
def admin_ui():
    return send_from_directory(os.path.join(BASE, 'admin'), 'index.html')

@app.route('/admin/<path:p>')
def admin_static(p):
    return send_from_directory(os.path.join(BASE, 'admin'), p)


# ── Book data (data.js) ────────────────────────────────────────────────────

@app.route('/api/data', methods=['GET'])
def api_get_data():
    try:
        text = open(apath('data.js'), encoding='utf-8').read()
        return jsonify(js_to_json(text))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data', methods=['PUT'])
def api_put_data():
    try:
        data = request.get_json(force=True)
        required = {'meta', 'novels', 'series', 'short_stories'}
        missing  = required - set(data.keys())
        if missing:
            return jsonify({'error': f'Refusing to save — data is missing keys: {missing}. '
                                     f'Reload the admin panel and try again.'}), 400
        write_data_js(data)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Book content files (synopsis/*.txt, books/*.md) ───────────────────────

@app.route('/api/content/<path:filepath>', methods=['GET'])
def api_get_content(filepath):
    norm = os.path.normpath(filepath).replace('\\', '/')
    if not (norm.startswith('synopsis/') or norm.startswith('books/')):
        abort(403)
    p = apath(*norm.split('/'))
    content = open(p, encoding='utf-8').read() if os.path.exists(p) else ''
    return jsonify({'content': content})

@app.route('/api/content/<path:filepath>', methods=['PUT'])
def api_put_content(filepath):
    norm = os.path.normpath(filepath).replace('\\', '/')
    if not (norm.startswith('synopsis/') or norm.startswith('books/')):
        abort(403)
    p = apath(*norm.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(request.get_json(force=True)['content'])
    return jsonify({'ok': True})


# ── Text files (synopsis/, about.txt, privacy-policy.txt) ─────────────────

@app.route('/api/texts')
def api_list_texts():
    result = []
    for lang in ['bg', 'en']:
        d = apath('synopsis', lang)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith('.txt'):
                    result.append({'lang': lang, 'file': f})
    return jsonify(result)

@app.route('/api/text/<lang>/<filename>', methods=['GET'])
def api_get_text(lang, filename):
    p = apath('synopsis', lang, filename)
    return jsonify({'content': open(p, encoding='utf-8').read() if os.path.exists(p) else ''})

@app.route('/api/text/<lang>/<filename>', methods=['PUT'])
def api_put_text(lang, filename):
    d = apath('synopsis', lang)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, filename), 'w', encoding='utf-8') as f:
        f.write(request.get_json(force=True)['content'])
    return jsonify({'ok': True})


# ── News ────────────────────────────────────────────────────────────────────

def news_index():
    p = apath('news', 'index.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []

def save_news_index(files):
    with open(apath('news', 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(files, f, ensure_ascii=False, indent=2)

@app.route('/api/news', methods=['GET'])
def api_list_news():
    return jsonify(news_index())

@app.route('/api/news/<lang>/<filename>', methods=['GET'])
def api_get_news(lang, filename):
    p = apath('news', lang, filename)
    return jsonify({'content': open(p, encoding='utf-8').read() if os.path.exists(p) else ''})

@app.route('/api/news', methods=['POST'])
def api_post_news():
    d = request.get_json(force=True)
    fname = d['filename']
    idx = news_index()
    if fname not in idx:
        idx.append(fname)
    save_news_index(idx)
    for lang, content in d.get('content', {}).items():
        dd = apath('news', lang)
        os.makedirs(dd, exist_ok=True)
        with open(os.path.join(dd, fname), 'w', encoding='utf-8') as f:
            f.write(content)
    return jsonify({'ok': True, 'filename': fname})

@app.route('/api/news/<filename>', methods=['DELETE'])
def api_del_news(filename):
    save_news_index([f for f in news_index() if f != filename])
    for lang in LANGS:
        p = apath('news', lang, filename)
        if os.path.exists(p):
            os.remove(p)
    return jsonify({'ok': True})


# ── Images ──────────────────────────────────────────────────────────────────

@app.route('/api/images/<lang>')
def api_list_images(lang):
    d = apath('images', lang)
    if not os.path.isdir(d):
        return jsonify([])
    return jsonify(sorted(
        f for f in os.listdir(d)
        if f.rsplit('.', 1)[-1].lower() in IMG_EXTS
    ))

@app.route('/api/upload/<lang>', methods=['POST'])
def api_upload(lang):
    f = request.files.get('file')
    if not f or not f.filename:
        return jsonify({'error': 'No file provided'}), 400
    ext = f.filename.rsplit('.', 1)[-1].lower()
    if ext not in IMG_EXTS:
        return jsonify({'error': f'File type .{ext} not allowed'}), 400

    stem = secure_filename(f.filename).rsplit('.', 1)[0]
    fname = f'{stem}.webp'
    d = apath('images', lang)
    os.makedirs(d, exist_ok=True)

    try:
        data, quality, dims = optimize_to_webp(f.stream)
    except Exception as e:
        return jsonify({'error': f'Could not process image: {e}'}), 400

    with open(os.path.join(d, fname), 'wb') as out:
        out.write(data)

    return jsonify({
        'ok': True, 'path': f'images/{lang}/{fname}', 'filename': fname,
        'size_kb': round(len(data) / 1024), 'quality': quality,
    })


# ── Static image preview (so the admin's <img> tags can load them) ────────

@app.route('/images/<path:p>')
def serve_image(p):
    return send_from_directory(apath('images'), p)


# ── Build (SSG) ─────────────────────────────────────────────────────────────

@app.route('/api/build', methods=['POST'])
def api_build():
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(BASE, 'scripts', 'build.py')],
            cwd=BASE, capture_output=True, text=True, timeout=120
        )
        return jsonify({
            'ok': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# ── Publish (git add/commit/push -> triggers GitHub Actions deploy) ─────────

@app.route('/api/publish', methods=['POST'])
def api_publish():
    import datetime

    def run(cmd):
        r = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, timeout=60)
        return r

    log = []
    try:
        r = run(['git', 'add', '-A'])
        log.append(f'$ git add -A\n{r.stdout}{r.stderr}')
        if r.returncode != 0:
            return jsonify({'ok': False, 'log': '\n'.join(log)})

        diff = run(['git', 'diff', '--cached', '--quiet'])
        if diff.returncode == 0:
            log.append('No changes to publish — dist/ and content are already up to date on GitHub.')
            return jsonify({'ok': True, 'nothing_to_publish': True, 'log': '\n'.join(log)})

        msg = f"Update site content ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"
        r = run(['git', 'commit', '-m', msg])
        log.append(f'$ git commit -m "{msg}"\n{r.stdout}{r.stderr}')
        if r.returncode != 0:
            return jsonify({'ok': False, 'log': '\n'.join(log)})

        r = run(['git', 'push'])
        log.append(f'$ git push\n{r.stdout}{r.stderr}')
        if r.returncode != 0:
            return jsonify({'ok': False, 'log': '\n'.join(log)})

        return jsonify({'ok': True, 'log': '\n'.join(log)})
    except Exception as e:
        log.append(f'Error: {e}')
        return jsonify({'ok': False, 'log': '\n'.join(log)}), 500


if __name__ == '__main__':
    print()
    print('  K.Z. Pendrake -- Admin')
    print('  -> http://localhost:8080/admin')
    print()
    app.run(port=8080, debug=False, use_reloader=False)
