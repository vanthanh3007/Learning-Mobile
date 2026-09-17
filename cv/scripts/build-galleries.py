#!/usr/bin/env python3
"""Quet thu muc anh va chen gallery vao cac trang HTML.

Chay sau khi da tai anh bang fetch-store-screenshots.py:

    python cv/scripts/build-galleries.py

Script se, voi moi thu muc trong cv/assets/projects/<slug>/ co anh:
  1. Tim trang co <section data-gallery="<slug>"> va thay noi dung bang luoi anh.
  2. Thay anh bia cua card tuong ung tren index.html.

Chay lai duoc nhieu lan (idempotent): moi lan deu dung lai section tu dau
theo danh sach file thuc te dang co, nen them/bot anh chi can chay lai.
"""

import os
import re
import struct
import sys

CV_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(CV_ROOT, "assets", "projects")
PAGES_DIR = os.path.join(CV_ROOT, "projects")
INDEX_PAGE = os.path.join(CV_ROOT, "index.html")

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

# Ten du an de dat vao alt text — alt phai mo ta duoc anh cho trinh doc man hinh.
DISPLAY_NAMES = {
    "sigo": "Sigo",
    "masu": "Masu",
    "masu-ship": "Masu Ship",
    "masu-driver": "Masu Driver",
    "masu-merchant": "Masu Merchant",
    "vfc-1-2": "VFC 1 & 2",
    "vfc-3-pestman": "VFC 3 — PestMan",
    "coshare": "Coshare",
    "hv-quan-ly-tai-san": "HV Quản Lý Tài Sản",
}

# Khi nhieu slug cung tro ve mot trang (Masu), slug dung truoc trong danh sach nay
# duoc chon lam anh bia tren trang chu. Ship la app nguoi dung cuoi nen dai dien tot nhat.
COVER_PRIORITY = ("masu-ship",)

SHOT_CLASSES = (
    "shot w-full rounded-xl border border-border bg-white "
    "hover:border-accent transition-colors duration-200"
)


def list_screenshots(slug):
    """Anh screenshot cua mot du an, da sap xep, bo qua icon."""
    folder = os.path.join(PROJECTS_DIR, slug)
    if not os.path.isdir(folder):
        return []
    names = [
        name
        for name in sorted(os.listdir(folder))
        if name.lower().endswith(IMAGE_EXTENSIONS) and not name.startswith("icon.")
    ]
    return names


def read_dimensions(path):
    """Kich thuoc anh doc tu magic bytes — de dat width/height chong nhay layout.

    Tu doc header thay vi dung Pillow: script phai chay duoc voi Python sach,
    khong bat nguoi dung cai them thu vien chi de sinh HTML tinh.
    """
    with open(path, "rb") as handle:
        head = handle.read(4096)

    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])

    if head[:2] == b"\xff\xd8":  # JPEG: duyet marker den khung SOF
        offset = 2
        while offset < len(head) - 9:
            if head[offset] != 0xFF:
                offset += 1
                continue
            marker = head[offset + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
                height, width = struct.unpack(">HH", head[offset + 5 : offset + 9])
                return width, height
            offset += 2 + struct.unpack(">H", head[offset + 2 : offset + 4])[0]

    if head[:4] == b"RIFF" and head[8:12] == b"WEBP" and head[12:16] == b"VP8X":
        width = int.from_bytes(head[24:27], "little") + 1
        height = int.from_bytes(head[27:30], "little") + 1
        return width, height

    return None


def grid_classes(first_image_size):
    """Chon so cot theo huong anh.

    Anh dien thoai (doc) xep 4 cot van doc duoc; anh chup web (ngang) ma nhet 4 cot
    thi chu trong anh nho den muc vo nghia — cho 2 cot.
    """
    if first_image_size and first_image_size[0] > first_image_size[1]:
        return "grid grid-cols-1 sm:grid-cols-2 gap-4 items-start"
    return "grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 items-start"


def build_gallery_section(slug, filenames, path_prefix):
    """Dung lai toan bo <section data-gallery> voi luoi anh that."""
    label = DISPLAY_NAMES.get(slug, slug)

    tiles = []
    first_size = None
    for index, name in enumerate(filenames, start=1):
        size = read_dimensions(os.path.join(PROJECTS_DIR, slug, name))
        if index == 1:
            first_size = size
        size_attributes = f'width="{size[0]}" height="{size[1]}" ' if size else ""
        tiles.append(
            '        <img data-lightbox loading="lazy" '
            f'src="{path_prefix}assets/projects/{slug}/{name}" '
            f"{size_attributes}"
            f'alt="{label} — màn hình {index}" '
            f'class="{SHOT_CLASSES}" />'
        )

    return (
        f'<section class="mb-12" data-gallery="{slug}">\n'
        '      <div class="flex items-baseline justify-between gap-4 mb-5">\n'
        '        <h2 class="font-heading font-semibold text-xs tracking-[0.2em] '
        f'uppercase text-muted">Giao diện — {label}</h2>\n'
        f'        <span class="no-print text-xs text-muted">{len(filenames)} ảnh · '
        'bấm để phóng to</span>\n'
        '      </div>\n'
        f'      <div class="{grid_classes(first_size)}">\n'
        + "\n".join(tiles)
        + "\n      </div>\n"
        "    </section>"
    )


def build_cover(slug, filenames):
    """Anh bia cho card tren trang chu.

    Anh doc (dien thoai): xep 3 cai canh nhau, cat tu dinh — ra dang "bo anh app".
    Anh ngang (chup web): mot anh trai kin khung, vi ghep 3 anh ngang vao ba cot
    hep thi moi anh chi con mot soc giua, khong nhan ra gi.
    """
    label = DISPLAY_NAMES.get(slug, slug)
    first_size = read_dimensions(os.path.join(PROJECTS_DIR, slug, filenames[0]))
    is_landscape = bool(first_size) and first_size[0] > first_size[1]

    if is_landscape:
        body = (
            f'            <img src="assets/projects/{slug}/{filenames[0]}" alt="" '
            'loading="lazy" class="w-full h-full object-cover object-top" />'
        )
        wrapper_classes = (
            "shot-cover aspect-[16/10] bg-zinc-100 border-b border-border overflow-hidden"
        )
    else:
        body = "\n".join(
            f'            <img src="assets/projects/{slug}/{name}" alt="" loading="lazy" '
            'class="w-1/3 h-full object-cover object-top rounded-t-lg shadow-sm" />'
            for name in filenames[:3]
        )
        wrapper_classes = (
            "shot-cover aspect-[16/10] bg-zinc-100 border-b border-border "
            "overflow-hidden flex items-end justify-center gap-2 px-4 pt-4"
        )

    return (
        f'<div class="{wrapper_classes}" '
        f'role="img" aria-label="Ảnh giao diện {label}">\n'
        f"{body}\n"
        "          </div>"
    )


def replace_block(html, pattern, replacement):
    """Thay dung mot khoi; tra ve (html_moi, da_thay_hay_chua)."""
    new_html, count = pattern.subn(lambda _: replacement, html, count=1)
    return new_html, count > 0


def main():
    if not os.path.isdir(PROJECTS_DIR):
        print("Chua co thu muc anh:", PROJECTS_DIR)
        return 1

    slugs = [
        name
        for name in sorted(os.listdir(PROJECTS_DIR))
        if os.path.isdir(os.path.join(PROJECTS_DIR, name)) and not name.startswith("_")
    ]
    slugs.sort(
        key=lambda s: (
            COVER_PRIORITY.index(s) if s in COVER_PRIORITY else len(COVER_PRIORITY),
            s,
        )
    )
    if not slugs:
        print("Chua co anh nao trong", PROJECTS_DIR)
        print("Chay fetch-store-screenshots.py truoc.")
        return 0

    index_html = open(INDEX_PAGE, encoding="utf-8").read()
    index_changed = False
    # Mot trang co the chua nhieu gallery (Masu = Ship + Driver + Merchant).
    # Anh bia tren trang chu chi lay tu slug dau tien khop voi trang do.
    covered_pages = set()

    for slug in slugs:
        filenames = list_screenshots(slug)
        if not filenames:
            print(f"[{slug}] thu muc rong — bo qua")
            continue

        # --- Gallery trong trang chi tiet ---
        gallery_pattern = re.compile(
            r'<section[^>]*data-gallery="' + re.escape(slug) + r'"[^>]*>.*?</section>',
            re.DOTALL,
        )
        matched_page = None
        for page_name in sorted(os.listdir(PAGES_DIR)):
            page_path = os.path.join(PAGES_DIR, page_name)
            page_html = open(page_path, encoding="utf-8").read()
            if not gallery_pattern.search(page_html):
                continue
            page_html, done = replace_block(
                page_html,
                gallery_pattern,
                build_gallery_section(slug, filenames, "../"),
            )
            if done:
                open(page_path, "w", encoding="utf-8").write(page_html)
                matched_page = page_name
            break

        # --- Anh bia tren trang chu ---
        # Chi thay dung card tro toi trang vua chen gallery, khong dung card khac.
        if matched_page and matched_page not in covered_pages:
            covered_pages.add(matched_page)
            card_pattern = re.compile(
                r'(<a href="projects/'
                + re.escape(matched_page)
                + r'"[^>]*>\s*)<div class="shot-cover.*?\n          </div>',
                re.DOTALL,
            )
            card_match = card_pattern.search(index_html)
            if card_match:
                # Giu nguyen the <a> mo dau (group 1), chi thay khoi anh bia.
                index_html = (
                    index_html[: card_match.start()]
                    + card_match.group(1)
                    + build_cover(slug, filenames)
                    + index_html[card_match.end() :]
                )
                index_changed = True

        print(
            f"[{slug}] {len(filenames)} anh -> "
            f"{matched_page or 'KHONG TIM THAY trang co data-gallery'}"
        )

    if index_changed:
        open(INDEX_PAGE, "w", encoding="utf-8").write(index_html)
        print("\nDa cap nhat anh bia tren index.html")

    print("Xong.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
