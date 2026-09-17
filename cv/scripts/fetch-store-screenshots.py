#!/usr/bin/env python3
"""Tai screenshot cua app tu Google Play / App Store ve thu muc assets.

Cach dung:
    python fetch-store-screenshots.py <slug> <store-url> [<store-url> ...]

Vi du:
    python fetch-store-screenshots.py sigo \
        "https://play.google.com/store/apps/details?id=com.sigo.app" \
        "https://apps.apple.com/vn/app/sigo/id1234567890"

Anh duoc luu vao: cv/assets/projects/<slug>/
    play-01.png, play-02.png, ...      (Google Play)
    appstore-01.png, appstore-02.png   (App Store)
    icon.png                            (icon app, neu lay duoc)

Ghi chu ve mang:
    Moi truong sandbox dung proxy MITM nen chung chi TLS khong verify duoc.
    Script tat verify (verify=False / ssl unverified context) de chay duoc.
    Chi tai anh cong khai tu CDN cua store nen rui ro chap nhan duoc.
"""

import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request

# Proxy sandbox MITM chung chi -> bo qua verify de request khong bi chan.
SSL_CONTEXT = ssl._create_unverified_context()

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}

ASSETS_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "projects"
)


def http_get(url, binary=False):
    """GET mot URL, tra ve bytes (binary=True) hoac str."""
    request = urllib.request.Request(url, headers=BROWSER_HEADERS)
    with urllib.request.urlopen(request, context=SSL_CONTEXT, timeout=45) as response:
        payload = response.read()
    return payload if binary else payload.decode("utf-8", errors="replace")


# --------------------------------------------------------------------------
# Google Play
# --------------------------------------------------------------------------

# Play danh dau screenshot bang thuoc tinh data-screenshot-index tren chinh the <img>.
# Day la moc dang tin cay duy nhat: hau to kich thuoc trong URL KHONG phan biet duoc
# screenshot voi icon hay anh "ung dung tuong tu" — ca ba deu co ca bien the doc lan ngang.
PLAY_SHOT_TAG_PATTERN = re.compile(
    r'<img[^>]*\bdata-screenshot-index="(\d+)"[^>]*>', re.IGNORECASE
)
PLAY_IMAGE_ID_PATTERN = re.compile(
    r"play-lh\.googleusercontent\.com/([A-Za-z0-9_\-]{20,})"
)
# Icon app luon dung hau to vuong dang "=s96"; screenshot dung "=wXXX-hYYY".
PLAY_ICON_PATTERN = re.compile(
    r"https://play-lh\.googleusercontent\.com/[A-Za-z0-9_\-]{20,}=s\d+"
)


def fetch_play_assets(store_url, limit=12):
    """Lay (screenshot_urls, icon_url) tu trang chi tiet app tren Google Play.

    Doc HTML mot lan duy nhat. Screenshot lay theo data-screenshot-index nen vua
    dung anh vua giu dung thu tu app da sap xep tren store.

    Ve kich thuoc: CDN play-lh chi resize xuong, khong phong to. Neu nha phat trien
    upload anh nho (vi du 384x512) thi moi hau to =w2560 / =s1600 deu tra ve dung
    ban goc do — khong co cach nao lay lon hon tu store.
    """
    html = http_get(_force_play_locale(store_url))

    indexed = []
    for tag_match in PLAY_SHOT_TAG_PATTERN.finditer(html):
        id_match = PLAY_IMAGE_ID_PATTERN.search(tag_match.group(0))
        if id_match:
            indexed.append((int(tag_match.group(1)), id_match.group(1)))
    indexed.sort(key=lambda pair: pair[0])

    seen = set()
    urls = []
    for _, image_id in indexed:
        if image_id in seen:
            continue
        seen.add(image_id)
        # =w2560 nghia la "cho ban lon nhat dang co"; CDN tu ha ve kich thuoc goc.
        urls.append(f"https://play-lh.googleusercontent.com/{image_id}=w2560")

    icon_match = PLAY_ICON_PATTERN.search(html)
    icon_url = re.sub(r"=s\d+$", "=s512", icon_match.group(0)) if icon_match else None

    return urls[:limit], icon_url


def _force_play_locale(store_url):
    """Ep locale VN de lay dung bo anh/mo ta ban Viet Nam."""
    parts = urllib.parse.urlsplit(store_url)
    query = dict(urllib.parse.parse_qsl(parts.query))
    query.update({"hl": "vi", "gl": "VN"})
    return urllib.parse.urlunsplit(
        parts._replace(query=urllib.parse.urlencode(query))
    )


# --------------------------------------------------------------------------
# App Store
# --------------------------------------------------------------------------

APPSTORE_ID_PATTERN = re.compile(r"/id(\d+)")
# Duoi URL mzstatic dang ".../392x696bb.png" quyet dinh kich thuoc anh tra ve.
MZSTATIC_SIZE_PATTERN = re.compile(r"/\d+x\d+[a-z]{0,2}\.(png|jpg|jpeg)$")


def fetch_appstore_assets(store_url):
    """Lay screenshot + icon qua iTunes Lookup API (chinh thong, on dinh hon scrape).

    Tra ve (screenshot_urls, icon_url).
    """
    id_match = APPSTORE_ID_PATTERN.search(store_url)
    if not id_match:
        raise ValueError("Khong tim thay app id trong URL App Store: " + store_url)

    country = _appstore_country(store_url)
    lookup_url = (
        "https://itunes.apple.com/lookup"
        f"?id={id_match.group(1)}&country={country}&entity=software"
    )
    results = json.loads(http_get(lookup_url)).get("results") or []
    if not results:
        raise ValueError("iTunes Lookup khong tra ve ket qua cho: " + store_url)

    app = results[0]
    screenshots = [_upscale_mzstatic(u, "1242x2688") for u in app.get("screenshotUrls", [])]
    icon = app.get("artworkUrl512") or app.get("artworkUrl100")
    return screenshots, icon


def _appstore_country(store_url):
    """Doan ma quoc gia tu duong dan /vn/app/... ; mac dinh vn."""
    segments = [s for s in urllib.parse.urlsplit(store_url).path.split("/") if s]
    if segments and len(segments[0]) == 2 and segments[0].isalpha():
        return segments[0].lower()
    return "vn"


def _upscale_mzstatic(url, size):
    """Doi hau to kich thuoc cua URL mzstatic sang ban do phan giai cao hon."""
    return MZSTATIC_SIZE_PATTERN.sub(lambda m: f"/{size}bb.{m.group(1)}", url)


# --------------------------------------------------------------------------
# Luu file
# --------------------------------------------------------------------------


def download_all(slug, play_url=None, appstore_url=None):
    target_dir = os.path.join(ASSETS_ROOT, slug)
    os.makedirs(target_dir, exist_ok=True)
    _clear_previous(target_dir, play_url is not None, appstore_url is not None)
    saved = []

    if play_url:
        print(f"[play] doc trang: {play_url}")
        screenshots, icon = fetch_play_assets(play_url)
        for index, url in enumerate(screenshots, start=1):
            saved.append(_save(url, target_dir, f"play-{index:02d}"))
        if icon:
            saved.append(_save(icon, target_dir, "icon"))

    if appstore_url:
        print(f"[appstore] lookup: {appstore_url}")
        screenshots, icon = fetch_appstore_assets(appstore_url)
        for index, url in enumerate(screenshots, start=1):
            saved.append(_save(url, target_dir, f"appstore-{index:02d}"))
        if icon and not any(os.path.basename(p).startswith("icon.") for p in saved):
            saved.append(_save(icon, target_dir, "icon"))

    print(f"\nXong: {len(saved)} file -> {target_dir}")
    return saved


def _clear_previous(target_dir, clear_play, clear_appstore):
    """Xoa anh cua lan chay truoc de so anh khong bi lech khi store bot anh."""
    prefixes = tuple(
        p for p, wanted in (("play-", clear_play), ("appstore-", clear_appstore), ("icon.", True))
        if wanted
    )
    for name in os.listdir(target_dir):
        if name.startswith(prefixes):
            os.remove(os.path.join(target_dir, name))


def _extension_of(data):
    """Doan duoi file tu magic bytes — Play tra ve ca PNG, JPEG lan WebP."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:2] == b"\xff\xd8":
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".png"


def _save(url, target_dir, stem):
    data = http_get(url, binary=True)
    filename = stem + _extension_of(data)
    path = os.path.join(target_dir, filename)
    with open(path, "wb") as handle:
        handle.write(data)
    print(f"  {filename:<18} {len(data) // 1024:>5} KB")
    return path


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1

    slug = argv[1]
    play_url = next((u for u in argv[2:] if "play.google.com" in u), None)
    appstore_url = next((u for u in argv[2:] if "apps.apple.com" in u or "itunes.apple.com" in u), None)

    if not play_url and not appstore_url:
        print("Loi: can it nhat mot link Google Play hoac App Store.")
        return 1

    download_all(slug, play_url, appstore_url)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
