from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "retroarch"))
from video import HEIGHT, TILE_COUNT, WIDTH, Tiles


class TileCacheTests(unittest.TestCase):
    def test_acknowledged_tiles_are_skipped_until_their_pixels_change(self):
        tiles = Tiles()
        frame = bytes(WIDTH * HEIGHT)
        for expected in range(TILE_COUNT):
            changed = tiles.next_changed(frame)
            assert changed is not None
            index, raw, _ = changed
            self.assertEqual(index, expected)
            tiles.sent[index] = raw
        self.assertIsNone(tiles.next_changed(frame))

        changed = tiles.next_changed(b"\xe0" + frame[1:])
        assert changed is not None
        index, raw, _ = changed
        self.assertEqual(index, 0)
        self.assertEqual(raw[0], 0xE0)
        tiles.sent[index] = raw
        self.assertIsNone(tiles.next_changed(b"\xe0" + frame[1:]))


if __name__ == "__main__":
    unittest.main()
