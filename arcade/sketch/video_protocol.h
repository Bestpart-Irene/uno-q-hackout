#pragma once

#include <stddef.h>
#include <stdint.h>

namespace ArcadeVideo {
constexpr int WIDTH = 160;
constexpr int HEIGHT = 120;
constexpr int TILE_WIDTH = 16;
constexpr int TILE_HEIGHT = 8;
constexpr int TILE_PIXELS = TILE_WIDTH * TILE_HEIGHT;
constexpr int TILE_COUNT = WIDTH * HEIGHT / TILE_PIXELS;

inline uint16_t rgb565(uint8_t value) {
  unsigned r = value >> 5, g = (value >> 2) & 7, b = value & 3;
  return ((r * 31 / 7) << 11) | ((g * 63 / 7) << 5) | (b * 31 / 3);
}

// Validate the complete packet before the caller draws anything.
inline bool decode(int tile, const uint8_t* data, size_t size, uint16_t* pixels) {
  if (tile < 0 || tile >= TILE_COUNT || size < 2 || size > TILE_PIXELS + 1) return false;
  uint8_t decoded[TILE_PIXELS];
  if (data[0] == 0) {
    if (size != TILE_PIXELS + 1) return false;
    for (int i = 0; i < TILE_PIXELS; ++i) decoded[i] = data[i + 1];
  } else if (data[0] == 1) {
    int used = 0;
    for (size_t i = 1; i < size; i += 2) {
      if (i + 1 >= size || data[i] == 0 || used + data[i] > TILE_PIXELS) return false;
      for (int j = 0; j < data[i]; ++j) decoded[used++] = data[i + 1];
    }
    if (used != TILE_PIXELS) return false;
  } else {
    return false;
  }
  for (int y = 0; y < TILE_HEIGHT * 2; ++y) {
    for (int x = 0; x < TILE_WIDTH * 2; ++x) {
      pixels[y * TILE_WIDTH * 2 + x] = rgb565(decoded[(y / 2) * TILE_WIDTH + x / 2]);
    }
  }
  return true;
}
}  // namespace ArcadeVideo
