"""Small RGB332 tiles for the sketch's 256-byte RPC receive limit."""

# shortcut: fixed low-resolution RGB332; increase only after measuring transport and drawing speed.
WIDTH, HEIGHT = 160, 120
TILE_WIDTH, TILE_HEIGHT = 16, 8
TILE_COUNT = WIDTH * HEIGHT // (TILE_WIDTH * TILE_HEIGHT)


def from_bgrx(data):
    if len(data) != WIDTH * HEIGHT * 4:
        raise ValueError("Expected a 160x120, 32-bit Xvfb image")
    return bytes((data[i + 2] & 0xE0) | ((data[i + 1] >> 3) & 0x1C) | (data[i] >> 6)
                 for i in range(0, len(data), 4))


def encode_tile(raw):
    if len(raw) != TILE_WIDTH * TILE_HEIGHT:
        raise ValueError("Invalid tile size")
    runs = bytearray([1])
    start = 0
    while start < len(raw):
        end = start + 1
        while end < len(raw) and raw[end] == raw[start]:
            end += 1
        runs.extend((end - start, raw[start]))
        start = end
    return bytes(runs) if len(runs) < len(raw) + 1 else b"\x00" + raw


class Tiles:
    def __init__(self):
        self.sent: list[bytes | None] = [None] * TILE_COUNT
        self.cursor = 0

    def next_changed(self, frame):
        if len(frame) != WIDTH * HEIGHT:
            raise ValueError("Invalid frame size")
        for _ in range(TILE_COUNT):
            index = self.cursor
            self.cursor = (index + 1) % TILE_COUNT
            x = (index % 10) * TILE_WIDTH
            y = (index // 10) * TILE_HEIGHT
            raw = b"".join(frame[(y + row) * WIDTH + x:(y + row) * WIDTH + x + TILE_WIDTH]
                           for row in range(TILE_HEIGHT))
            if raw != self.sent[index]:
                return index, raw, encode_tile(raw)
        return None
