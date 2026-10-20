#!/usr/bin/env python3
"""Render a favicon contact sheet at 16, 32, and 48 pixels.

The sheet is one horizontal row, 96 by 48. Smaller icons are vertically
centered on a transparent background. PNG encode and decode use the
standard library only. This script is a proof, not a CI check.

  python3 kit/favicon_sheet.py --src design-handoff/favicon-F1/apple-touch-icon.png --out /tmp/favicon-sheet.png
"""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

SIZES = (16, 32, 48)
SHEET_WIDTH = sum(SIZES)
SHEET_HEIGHT = max(SIZES)
_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def _paeth(left: int, up: int, up_left: int) -> int:
    estimate = left + up - up_left
    dist_left = abs(estimate - left)
    dist_up = abs(estimate - up)
    dist_up_left = abs(estimate - up_left)
    if dist_left <= dist_up and dist_left <= dist_up_left:
        return left
    if dist_up <= dist_up_left:
        return up
    return up_left


def _unfilter(raw: bytes, width: int, height: int, bpp: int) -> list[bytearray]:
    stride = width * bpp
    expected = height * (stride + 1)
    if len(raw) != expected:
        raise SystemExit(f"PNG image data length {len(raw)} != {expected}")
    rows: list[bytearray] = []
    prev = bytearray(stride)
    offset = 0
    for _ in range(height):
        filt = raw[offset]
        offset += 1
        scan = bytearray(raw[offset : offset + stride])
        offset += stride
        recon = bytearray(stride)
        if filt == 0:
            recon[:] = scan
        elif filt == 1:
            for i in range(stride):
                left = recon[i - bpp] if i >= bpp else 0
                recon[i] = (scan[i] + left) & 255
        elif filt == 2:
            for i in range(stride):
                recon[i] = (scan[i] + prev[i]) & 255
        elif filt == 3:
            for i in range(stride):
                left = recon[i - bpp] if i >= bpp else 0
                recon[i] = (scan[i] + ((left + prev[i]) // 2)) & 255
        elif filt == 4:
            for i in range(stride):
                left = recon[i - bpp] if i >= bpp else 0
                up_left = prev[i - bpp] if i >= bpp else 0
                recon[i] = (scan[i] + _paeth(left, prev[i], up_left)) & 255
        else:
            raise SystemExit(f"unsupported PNG filter {filt}")
        prev = recon
        rows.append(recon)
    return rows


def read_png(path: Path) -> tuple[int, int, list[list[tuple[int, int, int, int]]]]:
    data = Path(path).read_bytes()
    if not data.startswith(_SIGNATURE):
        raise SystemExit(f"{path} is not a PNG")
    offset = 8
    width = height = bit = color = interlace = None
    idat = bytearray()
    while offset + 12 <= len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        tag = data[offset + 4 : offset + 8]
        start = offset + 8
        end = start + length
        if end + 4 > len(data):
            raise SystemExit(f"{path} has a truncated PNG chunk")
        chunk = data[start:end]
        crc_got = struct.unpack_from(">I", data, end)[0]
        crc_exp = zlib.crc32(tag + chunk) & 0xFFFFFFFF
        if crc_got != crc_exp:
            raise SystemExit(f"{path} has a bad CRC for {tag!r}")
        offset = end + 4
        if tag == b"IHDR":
            width, height, bit, color, _comp, _filt, interlace = struct.unpack(">IIBBBBB", chunk)
        elif tag == b"IDAT":
            idat.extend(chunk)
        elif tag == b"IEND":
            break
    if width is None or height is None or bit is None or color is None or interlace is None:
        raise SystemExit(f"{path} is missing IHDR")
    if bit != 8 or color not in (2, 6) or interlace != 0:
        raise SystemExit(
            f"unsupported PNG {path}: {width}x{height} bit={bit} color={color} interlace={interlace}"
        )
    bpp = 4 if color == 6 else 3
    rows = _unfilter(zlib.decompress(bytes(idat)), width, height, bpp)
    pixels: list[list[tuple[int, int, int, int]]] = []
    for row in rows:
        pix_row: list[tuple[int, int, int, int]] = []
        for x in range(width):
            i = x * bpp
            if bpp == 4:
                pix_row.append((row[i], row[i + 1], row[i + 2], row[i + 3]))
            else:
                pix_row.append((row[i], row[i + 1], row[i + 2], 255))
        pixels.append(pix_row)
    return width, height, pixels


def write_png(
    path: Path,
    width: int,
    height: int,
    pixels: list[list[tuple[int, int, int, int]]],
) -> None:
    raw = bytearray()
    for row in pixels:
        if len(row) != width:
            raise SystemExit(f"PNG row width {len(row)} != {width}")
        raw.append(0)
        for red, green, blue, alpha in row:
            raw.extend((red & 255, green & 255, blue & 255, alpha & 255))
    if len(pixels) != height:
        raise SystemExit(f"PNG height {len(pixels)} != {height}")
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    compressed = zlib.compress(bytes(raw), 9)
    blob = _SIGNATURE + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", compressed) + _chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)


def _scale(
    pixels: list[list[tuple[int, int, int, int]]],
    src_w: int,
    src_h: int,
    dst_w: int,
    dst_h: int,
) -> list[list[tuple[int, int, int, int]]]:
    scaled: list[list[tuple[int, int, int, int]]] = []
    for y in range(dst_h):
        sy = min(src_h - 1, ((y * 2 + 1) * src_h) // (dst_h * 2))
        row: list[tuple[int, int, int, int]] = []
        for x in range(dst_w):
            sx = min(src_w - 1, ((x * 2 + 1) * src_w) // (dst_w * 2))
            row.append(pixels[sy][sx])
        scaled.append(row)
    return scaled


def _compose(
    pixels: list[list[tuple[int, int, int, int]]],
    src_w: int,
    src_h: int,
) -> list[list[tuple[int, int, int, int]]]:
    canvas = [[(0, 0, 0, 0) for _ in range(SHEET_WIDTH)] for _ in range(SHEET_HEIGHT)]
    x0 = 0
    for size in SIZES:
        scaled = _scale(pixels, src_w, src_h, size, size)
        y0 = (SHEET_HEIGHT - size) // 2
        for y in range(size):
            for x in range(size):
                canvas[y0 + y][x0 + x] = scaled[y][x]
        x0 += size
    return canvas


def render_favicon_sheet(src: Path, dest: Path) -> None:
    width, height, pixels = read_png(src)
    write_png(dest, SHEET_WIDTH, SHEET_HEIGHT, _compose(pixels, width, height))


def default_src(root: Path) -> Path:
    folder = root / "design-handoff" / "favicon-F1"
    preferred = folder / "apple-touch-icon.png"
    if preferred.is_file():
        return preferred
    fallback = folder / "icon-192.png"
    if fallback.is_file():
        return fallback
    raise SystemExit(f"missing {preferred}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=None, help="source PNG (default: apple touch icon)")
    parser.add_argument("--out", type=Path, required=True, help="contact sheet PNG to write")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    src = args.src if args.src is not None else default_src(root)
    render_favicon_sheet(src, args.out)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
