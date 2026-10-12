"""Split/reassemble a large packed scene using checked portable binary parts."""
import argparse
import json
import uuid
from pathlib import Path

from common import sha256, write_json

PART_BYTES = 40 * 1024 * 1024


def split(template, folder):
    manifest_path = folder / 'template-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if sha256(template) != manifest['sha256']:
        raise RuntimeError('Input does not match the reviewed template manifest')
    parts = []
    with template.open('rb') as source:
        index = 1
        while data := source.read(PART_BYTES):
            name = manifest['template_file'] + f'.part{index:02}'
            path = folder / name
            path.write_bytes(data)
            parts.append({'file': name, 'bytes': len(data), 'sha256': sha256(path)})
            index += 1
    manifest['template_parts'] = parts
    write_json(manifest_path, manifest)
    return manifest


def assemble(folder, cache):
    manifest = json.loads((folder / 'template-manifest.json').read_text())
    name = manifest['template_file']
    if Path(name).name != name:
        raise ValueError('Template filename must be a basename')
    # Older unsplit assets remain supported for privately maintained templates.
    if not manifest.get('template_parts'):
        template = folder / name
        if sha256(template) != manifest['sha256']:
            raise RuntimeError('Template hash mismatch')
        return template, manifest
    cache = cache / 'templates' / manifest['sha256']
    template = cache / name
    if template.exists() and sha256(template) == manifest['sha256']:
        return template, manifest
    cache.mkdir(parents=True, exist_ok=True)
    temporary = cache / (name + '.' + uuid.uuid4().hex + '.partial')
    try:
        with temporary.open('wb') as dest:
            for part in manifest['template_parts']:
                if Path(part['file']).name != part['file']:
                    raise ValueError('Part filenames must be basenames')
                path = folder / part['file']
                if not path.exists() or path.stat().st_size != part['bytes'] or sha256(path) != part['sha256']:
                    raise RuntimeError('Template part missing or corrupt: ' + part['file'])
                with path.open('rb') as source:
                    while data := source.read(1024 * 1024):
                        dest.write(data)
        if temporary.stat().st_size != manifest['file_bytes'] or sha256(temporary) != manifest['sha256']:
            raise RuntimeError('Reassembled template hash mismatch')
        temporary.replace(template)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return template, manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=['split', 'assemble'])
    p.add_argument('--folder', type=Path, required=True)
    p.add_argument('--template', type=Path)
    p.add_argument('--cache', type=Path)
    a = p.parse_args()
    if a.stage == 'split':
        if not a.template:
            p.error('--template is required for split')
        split(a.template, a.folder)
    else:
        if not a.cache:
            p.error('--cache is required for assemble')
        print(assemble(a.folder, a.cache)[0])
