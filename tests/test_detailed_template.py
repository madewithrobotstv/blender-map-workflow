"""Check the distributable input and prevent silent geography changes in template mode."""
import copy
import json
import sys
import unittest
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blender-map-workflow' / 'scripts'))
from common import sha256
from detailed import validate
from template_assets import assemble


class DetailedTemplateTests(unittest.TestCase):
    def test_template_is_real_complete_content_matching_manifest(self):
        folder = ROOT / 'blender-map-workflow' / 'templates'
        manifest = json.loads((folder / 'template-manifest.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            template, actual = assemble(folder, Path(directory))
            self.assertEqual(template.stat().st_size, manifest['file_bytes'])
            self.assertEqual(sha256(template), manifest['sha256'])
        self.assertEqual(manifest['collections']['08_COUNTIES'], 100)
        self.assertEqual(manifest['collections']['09_WATERBODIES'], 315)

    def test_corrupt_part_is_rejected_and_partial_cache_removed(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'input'
            folder.mkdir()
            payload = b'reviewed-content'
            manifest = {'template_file': 'test.blend', 'file_bytes': len(payload),
                        'sha256': hashlib.sha256(payload).hexdigest(),
                        'template_parts': [{'file': 'test.blend.part01',
                                            'bytes': len(payload),
                                            'sha256': hashlib.sha256(payload).hexdigest()}]}
            (folder / 'template-manifest.json').write_text(json.dumps(manifest))
            (folder / 'test.blend.part01').write_bytes(b'changed-content')
            with self.assertRaisesRegex(RuntimeError, 'missing or corrupt'):
                assemble(folder, root / 'cache')
            self.assertFalse(list((root / 'cache').rglob('*.partial')))
            self.assertFalse(list((root / 'cache').rglob('test.blend')))

    def test_state_panel_configuration_cannot_silently_relabel_snapshot(self):
        config = json.loads((ROOT / 'blender-map-workflow' / 'presets' / 'north-carolina-detailed.json').read_text())
        validate(config)
        wrong_state = copy.deepcopy(config)
        wrong_state['panels'] = [{'states': ['23']}]
        with self.assertRaisesRegex(ValueError, 'Unsupported detailed configuration'):
            validate(wrong_state)


if __name__ == '__main__':
    unittest.main()
