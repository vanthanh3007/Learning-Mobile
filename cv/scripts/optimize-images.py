"""Nen anh trong cv/assets ve kich thuoc thuc su can dung tren web.

Ly do: anh tai truc tiep tu Google Play / App Store co do phan giai gap 2-3 lan
muc trang CV hien thi. Lightbox gioi han max-width 72rem (1152px) nen anh
2560px la lang phi bang thong hoan toan.

Chay:  python cv/scripts/optimize-images.py          # xem truoc, khong ghi de
       python cv/scripts/optimize-images.py --apply  # ghi de that

Script idempotent: chay lai tren anh da nen se bo qua (anh da nho hon nguong).
Ten file va duoi file GIU NGUYEN de khong phai sua HTML.
"""

import argparse
import io
import os
import sys

from PIL import Image

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

# (glob thu muc, chieu rong toi da, chat luong JPEG)
# Anh web chup man hinh desktop: 1600px du cho lightbox 1152px tren man retina.
# Anh dien thoai 720px: giu nguyen kich thuoc, chi nen lai.
RULES = [
    ("projects/coshare", 1600, 80),
    ("projects/hv-quan-ly-tai-san", 1600, 80),
    ("projects/masu-ship", 720, 78),
    ("projects/masu-driver", 720, 78),
    ("projects/masu-merchant", 720, 78),
    ("projects/sigo", 384, 82),
    ("projects/vfc-1-2", 256, 82),
    ("projects/vfc-3-pestman", 256, 82),
    ("img", 480, 85),
]

# Icon app chi hien thi toi da 80px (w-20) nen 256px la thua du cho man retina 3x.
ICON_MAX = 256

EXTS = (".png", ".jpg", ".jpeg")


def encode_jpeg(im, quality):
    if im.mode != "RGB":
        im = im.convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True, subsampling=1)
    return buf.getvalue()


def encode_png(im):
    """Thu ca PNG 8-bit (quantize) lan PNG goc, lay ban nho hon.

    Anh chup man hinh app thuong it mau nen quantize 256 mau gan nhu khong
    nhin thay khac biet, trong khi dung luong giam manh.
    """
    candidates = []

    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    candidates.append(buf.getvalue())

    try:
        has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
        q = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE if has_alpha else Image.Quantize.MEDIANCUT)
        buf = io.BytesIO()
        q.save(buf, "PNG", optimize=True)
        candidates.append(buf.getvalue())
    except Exception:
        pass

    return min(candidates, key=len)


def process(path, max_width, quality, apply_changes):
    before = os.path.getsize(path)
    ext = os.path.splitext(path)[1].lower()

    with Image.open(path) as im:
        im.load()
        w, h = im.size

        if w > max_width:
            new_h = round(h * max_width / w)
            im = im.resize((max_width, new_h), Image.LANCZOS)

        data = encode_png(im) if ext == ".png" else encode_jpeg(im, quality)
        out_size = im.size

    # Chi ghi khi thuc su nho hon — tranh lam anh phinh ra khi chay lai.
    if len(data) >= before:
        return (before, before, (w, h), (w, h), False)

    if apply_changes:
        with open(path, "wb") as f:
            f.write(data)

    return (before, len(data), (w, h), out_size, True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="ghi de file that (mac dinh chi xem truoc)")
    args = ap.parse_args()

    total_before = total_after = 0
    changed = []
    resized = []

    for subdir, max_width, quality in RULES:
        d = os.path.normpath(os.path.join(ASSETS, subdir))
        if not os.path.isdir(d):
            print(f"  bo qua (khong co): {subdir}", file=sys.stderr)
            continue

        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(EXTS):
                continue
            path = os.path.join(d, fn)
            limit = ICON_MAX if fn.lower().startswith("icon") else max_width

            before, after, dim_in, dim_out, did = process(path, limit, quality, args.apply)
            total_before += before
            total_after += after
            rel = os.path.relpath(path, ASSETS).replace(os.sep, "/")

            if did:
                pct = 100 - after * 100 // before
                note = f"  {dim_in[0]}x{dim_in[1]} -> {dim_out[0]}x{dim_out[1]}" if dim_in != dim_out else ""
                changed.append(f"  -{pct:3d}%  {before // 1024:5d} -> {after // 1024:4d} KB  {rel}{note}")
                if dim_in != dim_out:
                    resized.append((rel, dim_in, dim_out))

    print("\n".join(changed))
    print()
    print(f"Tong: {total_before / 1024 / 1024:.2f} MB -> {total_after / 1024 / 1024:.2f} MB "
          f"(giam {100 - total_after * 100 // total_before}%)")

    if resized:
        print("\nAnh DOI kich thuoc — phai sua thuoc tinh width/height trong HTML:")
        for rel, a, b in resized:
            print(f'  {rel}: width="{a[0]}" height="{a[1]}"  ->  width="{b[0]}" height="{b[1]}"')

    if not args.apply:
        print("\n(xem truoc — chua ghi file nao. Them --apply de ap dung)")


if __name__ == "__main__":
    main()
