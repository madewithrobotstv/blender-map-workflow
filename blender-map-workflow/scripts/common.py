"""Portable configuration, checked downloads, and grid sampling (no bpy)."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.partial')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_config(path):
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    if config.get('schema_version') != 1:
        raise ValueError('Expected schema_version: 1')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', config['slug']):
        raise ValueError('slug must contain lowercase letters, digits, and hyphens')
    if not config.get('panels') or config.get('metres_per_unit', 0) <= 0:
        raise ValueError('At least one panel and positive metres_per_unit are required')
    ids = [p['id'] for p in config['panels']]
    if len(set(ids)) != len(ids) or any(not re.fullmatch(r'[a-z0-9-]+', s) for s in ids):
        raise ValueError('Panel ids must be unique lowercase slugs')
    for p in config['panels']:
        if not 16 <= p['mesh_width'] <= p['texture_width'] <= 8000:
            raise ValueError('Require 16 <= mesh_width <= texture_width <= 8000')
        if p['scale'] <= 0 or p['relief'] <= 0:
            raise ValueError('Panel scale and relief must be positive')
    return config


def download(url, path, offline=False):
    """Cache by request URL; never trust partial responses or an unrelated old file."""
    path = Path(path)
    meta = path.with_suffix(path.suffix + '.source.json')
    if path.exists() and meta.exists():
        record = json.loads(meta.read_text())
        if record['url'] == url and record['sha256'] == sha256(path):
            return record
    if offline:
        raise RuntimeError(f'Offline cache missing or invalid: {path.name}')
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.partial')
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'BlenderMapWorkflow/1.0'})
            with urllib.request.urlopen(request, timeout=180) as response, tmp.open('wb') as out:
                shutil.copyfileobj(response, out)
            if tmp.stat().st_size == 0:
                raise RuntimeError('Empty source response')
            tmp.replace(path)
            record = {'url': url, 'acquired_utc': datetime.now(timezone.utc).isoformat(),
                      'sha256': sha256(path), 'bytes': path.stat().st_size}
            write_json(meta, record)
            return record
        except Exception:
            tmp.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def discover_blender(explicit=None):
    candidates = [explicit, os.environ.get('BLENDER_BIN'), shutil.which('blender')]
    if os.name == 'nt':
        candidates.extend(str(p) for p in sorted(Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')).glob('Blender Foundation/Blender */blender.exe'), reverse=True))
    else:
        candidates.extend(str(p) for p in sorted(Path('/Applications').glob('Blender*.app/Contents/MacOS/Blender'), reverse=True))
    checked = []
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file():
            continue
        result = subprocess.run([candidate, '--version'], capture_output=True, text=True)
        version = next((s for s in result.stdout.splitlines() if s.startswith('Blender ')), '')
        checked.append(version)
        if version and not any(s in version.lower() for s in ('alpha', 'beta', 'candidate')):
            match = re.search(r'Blender (\d+)\.(\d+)', version)
            if match and tuple(map(int, match.groups())) >= (4, 5):
                return str(Path(candidate).resolve()), version
    raise RuntimeError(f'Blender stable >= 4.5 not found. Set BLENDER_BIN or --blender. Checked: {checked}')


def sample_surface(elevation, bounds, x, y):
    """Sample the same diagonal used by build_scene triangles; rows run north to south."""
    import numpy as np
    h, w = elevation.shape
    u = np.clip((np.asarray(x) - bounds[0]) / (bounds[2] - bounds[0]) * (w - 1), 0, w - 1)
    v = np.clip((bounds[3] - np.asarray(y)) / (bounds[3] - bounds[1]) * (h - 1), 0, h - 1)
    i = np.minimum(u.astype(int), w - 2)
    j = np.minimum(v.astype(int), h - 2)
    tx, ty = u - i, v - j
    a, b, c, d = elevation[j, i], elevation[j, i + 1], elevation[j + 1, i], elevation[j + 1, i + 1]
    return np.where(tx + ty <= 1, a * (1 - tx - ty) + b * tx + c * ty,
                    d * (tx + ty - 1) + b * (1 - ty) + c * (1 - tx))
