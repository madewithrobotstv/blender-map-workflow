"""Meaningful invariants behind overlay alignment and offline source integrity."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'blender-map-workflow'/'scripts'))
from common import download, sample_surface


class GeometryTests(unittest.TestCase):
    def test_overlay_uses_triangle_surface_instead_of_bilinear_average(self):
        # The diagonal between heights 10 and 20 is 15 at the midpoint.
        # A bilinear DEM sampler would give 7.5 and sink the overlay into this mesh.
        terrain=np.array([[0.,10.],[20.,0.]])
        result=sample_surface(terrain,[100.,200.,110.,210.],105.,205.)
        self.assertAlmostEqual(float(result),15.)

    def test_north_to_south_grid_and_large_projected_origin(self):
        terrain=np.array([[1.,2.,3.],[4.,5.,6.],[7.,8.,9.]])
        bounds=[1_000_000.,2_000_000.,1_000_020.,2_000_020.]
        x=np.array([bounds[0],bounds[2],bounds[0],bounds[2],1_000_010.])
        y=np.array([bounds[3],bounds[3],bounds[1],bounds[1],2_000_010.])
        np.testing.assert_allclose(sample_surface(terrain,bounds,x,y),[1,3,7,9,5])


class CacheTests(unittest.TestCase):
    def test_offline_cache_reuses_only_matching_checked_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'original.bin';source.write_bytes(b'authoritative source sample')
            cached=root/'cache.bin';url=source.as_uri()
            first=download(url,cached)
            source.unlink()  # Offline repeat must work without original source.
            self.assertEqual(download(url,cached,offline=True)['sha256'],first['sha256'])
            cached.write_bytes(b'tampered or truncated')
            with self.assertRaisesRegex(RuntimeError,'Offline cache missing or invalid'):
                download(url,cached,offline=True)
            # An unrelated URL cannot reuse a file just because its filename matches.
            with self.assertRaises(RuntimeError):
                download('file:///another-source.bin',cached,offline=True)


if __name__=='__main__':unittest.main()
