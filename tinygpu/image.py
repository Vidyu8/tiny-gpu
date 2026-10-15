"""Dependency-free PNG writer (grayscale, nearest-neighbour upscale)."""
import struct, zlib

def write_png(path, pixels, w, h, scale=16):
    rows = []
    for y in range(h):
        row = bytes(min(255, p & 0xFFFF) for p in pixels[y * w:(y + 1) * w])
        row = b"".join(bytes([p]) * scale for p in row)
        rows += [b"\x00" + row] * scale
    raw = b"".join(rows)
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w * scale, h * scale, 8, 0, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
