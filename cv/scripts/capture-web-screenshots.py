#!/usr/bin/env python3
"""Chup man hinh du an web bang Playwright, luu vao thu muc assets.

Dung cho cac du an KHONG co tren store (Coshare, HV Quan Ly Tai San...).

Cach dung
---------
1) Trang cong khai — chup thang:

    python cv/scripts/capture-web-screenshots.py coshare https://coshare.vn/ https://coshare.vn/tong-quan

2) Trang phai dang nhap — dang nhap mot lan, cac lan sau dung lai phien do:

    python cv/scripts/capture-web-screenshots.py hv-quan-ly-tai-san --login https://hvassets.example/login
    (trinh duyet mo len, ban tu dang nhap, xong quay lai terminal bam Enter)

    python cv/scripts/capture-web-screenshots.py hv-quan-ly-tai-san --auth https://hvassets.example/dashboard ...

Tham so khac
------------
    --full          chup tron trang (mac dinh chi chup khung nhin 1280x900)
    --mobile        chup o khung dien thoai 390x844
    --wait 3000     cho them mili giay truoc khi chup (trang co animation)
    --jpeg          luu JPEG thay vi PNG — nhe hon nhieu lan voi trang nhieu anh chup,
                    doi lai chu nho hoi mo. Trang thuan giao dien thi de PNG.
    --redact        lam mo chu trong bang du lieu / the thong ke truoc khi chup.
                    BAT BUOC voi app chay du lieu that cua khach hang: bo cuc, mau sac,
                    icon van ro — chi rieng noi dung chu bi mo thanh vet.
    --redact-selector "..."   them CSS selector can che (dung duoc nhieu lan)
    --redact-all    che TOAN BO chu, chi chua lai menu / tieu de / nut bam.
                    Dung khi app khong co cau truc nao doan duoc dau la du lieu
                    (Tailwind thuan, khong <table>) — an toan nhung anh kho doc hon.
    --keep-selector "..."     chua lai mot vung khoi --redact-all (dung nhieu lan)
    --click-nav "Tai san"     sau khi chup het URL thi bam menu co chu nay roi chup tiep.
                    Danh cho route mo truc tiep bi loi nhung vao bang menu thi duoc.

Phien dang nhap luu o cv/scripts/.auth/<slug>.json — thu muc nay da bi .gitignore
chan vi chua cookie that, khong duoc commit.
"""

import argparse
import os
import sys

CV_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_ROOT = os.path.join(CV_ROOT, "assets", "projects")
AUTH_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".auth")

DESKTOP_VIEWPORT = {"width": 1280, "height": 900}
MOBILE_VIEWPORT = {"width": 390, "height": 844}

# Noi thuong chua du lieu that: o trong bang, so lieu trong the thong ke, nhan bieu do.
# KHONG che thanh dieu huong, tieu de cot, nut bam — do la phan can khoe trong CV.
REDACT_SELECTORS = (
    "tbody td",
    "tbody th",
    '[role="row"] [role="cell"]',
    '[role="gridcell"]',
    ".recharts-text",
    ".ant-statistic-content",
    ".ant-descriptions-item-content",
)

# Che bang cach bo mau chu va thay bang text-shadow: chu thanh vet mo khong doc duoc,
# nhung khung bang, duong ke, icon SVG va mau nen deu giu nguyen do khong phai chu.
# Dung filter:blur() se lam mo ca o va lam anh trong nhu bi loi.
# Do mo tinh bang em chu khong phai px: chu cang to cang can mo nhieu. Dat 7px cung
# thi chu 14px bien mat nhung so lieu co 36px van doc duoc nguyen ven.
REDACT_RULE = (
    "color: transparent !important;"
    "text-shadow: 0 0 0.45em rgba(63, 63, 70, 0.8) !important;"
)


def redaction_css(extra_selectors=()):
    selectors = list(REDACT_SELECTORS) + list(extra_selectors)
    # Che ca the con: chu that hay nam trong <span>/<a> ben trong o, khong nam truc tiep.
    targets = ", ".join(selectors + [f"{s} *" for s in selectors])
    return f"{targets} {{ {REDACT_RULE} }}"


# Nhung phan la KHUNG giao dien chu khong phai du lieu — giu ro de anh con y nghia
# trong CV. Moi thu con lai bi che. Whitelist chu khong blacklist: app dung Tailwind
# thuan thi khong co class nao dang tin de doan "day la du lieu nhay cam".
REDACT_ALL_KEEP = (
    "nav a",
    "aside nav a",
    '[role="navigation"] a',
    '[role="tab"]',
    "h1",
    "h2",
    "thead th",
    "button",
    "label",
)


def redaction_all_css(keep_selectors=()):
    keep = list(REDACT_ALL_KEEP) + list(keep_selectors)
    keep_targets = ", ".join(keep + [f"{s} *" for s in keep])
    return (
        # Anh dai dien co the la mat nguoi that — che bang blur chu khong phai text-shadow.
        "img, [style*='background-image'] { filter: blur(6px) !important; }\n"
        f"body * {{ {REDACT_RULE} }}\n"
        f"{keep_targets} {{ color: #18181b !important; text-shadow: none !important; }}\n"
        # Logo/icon dieu huong khong phai du lieu, tra lai do net.
        "nav img, aside img, header svg, nav svg, aside svg { filter: none !important; }"
    )


def auth_state_path(slug):
    return os.path.join(AUTH_ROOT, f"{slug}.json")


def run_login(slug, login_url):
    """Mo trinh duyet that de nguoi dung tu dang nhap, roi luu lai phien."""
    from playwright.sync_api import sync_playwright

    os.makedirs(AUTH_ROOT, exist_ok=True)
    with sync_playwright() as play:
        browser = play.chromium.launch(headless=False)
        context = browser.new_context(viewport=DESKTOP_VIEWPORT)
        page = context.new_page()
        page.goto(login_url, wait_until="domcontentloaded", timeout=60_000)

        print("\n  Trinh duyet da mo. Dang nhap xong thi quay lai day bam Enter.")
        input("  Bam Enter khi da dang nhap xong... ")

        context.storage_state(path=auth_state_path(slug))
        browser.close()

    print(f"\nDa luu phien dang nhap: {auth_state_path(slug)}")
    print("Lan sau chay kem co --auth de dung lai phien nay.")


def capture(
    slug,
    urls,
    use_auth=False,
    full_page=False,
    mobile=False,
    wait_ms=1500,
    jpeg=False,
    redact=False,
    redact_selectors=(),
    redact_all=False,
    keep_selectors=(),
    click_nav=(),
):
    from playwright.sync_api import sync_playwright

    target_dir = os.path.join(ASSETS_ROOT, slug)
    os.makedirs(target_dir, exist_ok=True)

    storage_state = None
    if use_auth:
        storage_state = auth_state_path(slug)
        if not os.path.exists(storage_state):
            print(f"Chua co phien dang nhap cho '{slug}'. Chay --login truoc.")
            return 1

    # Xoa anh web cu de so thu tu khong bi lech khi bot/them URL.
    for name in os.listdir(target_dir):
        if name.startswith("web-"):
            os.remove(os.path.join(target_dir, name))

    with sync_playwright() as play:
        browser = play.chromium.launch()
        context = browser.new_context(
            viewport=MOBILE_VIEWPORT if mobile else DESKTOP_VIEWPORT,
            device_scale_factor=2,  # anh net tren man hinh retina
            storage_state=storage_state,
            locale="vi-VN",
        )
        page = context.new_page()

        counter = {"index": 0}

        def shoot(note):
            """Cho trang on dinh, che du lieu, roi luu anh. Tra ve True neu da luu."""
            counter["index"] += 1
            filename = f"web-{counter['index']:02d}." + ("jpg" if jpeg else "png")
            path = os.path.join(target_dir, filename)

            page.wait_for_timeout(wait_ms)

            # Chen sau khi trang da render: SPA thay DOM lien tuc, chen som se bi ghi de.
            if redact_all:
                page.add_style_tag(content=redaction_all_css(keep_selectors))
            elif redact:
                page.add_style_tag(content=redaction_css(redact_selectors))
            if redact or redact_all:
                page.wait_for_timeout(250)

            shot_options = {"path": path, "full_page": full_page}
            if jpeg:
                shot_options.update(type="jpeg", quality=82)
            page.screenshot(**shot_options)
            print(f"  {filename:<12} {os.path.getsize(path) // 1024:>5} KB  {note}")
            return True

        saved = 0
        for url in urls:
            try:
                page.goto(url, wait_until="networkidle", timeout=60_000)
            except Exception as error:
                # networkidle hay treo o trang co polling/websocket — thu lai nhe hon.
                print(f"  {url} -> networkidle that bai ({type(error).__name__}), thu domcontentloaded")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                except Exception as fatal:
                    print(f"  BO QUA {url}: {str(fatal).splitlines()[0][:90]}")
                    continue
            saved += shoot(url)

        # Route bi server chan khi mo truc tiep (vi du /assets dung ten voi thu muc
        # static) van vao duoc bang cach bam menu trong app — router chay o client.
        for label in click_nav:
            try:
                page.get_by_role("link", name=label, exact=False).first.click(timeout=15_000)
                page.wait_for_timeout(600)
            except Exception as error:
                print(f"  BO QUA menu '{label}': {type(error).__name__}")
                continue
            saved += shoot(f"[menu] {label} -> {page.url}")

        browser.close()

    print(f"\nXong: {saved} anh -> {target_dir}")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("slug")
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--login", metavar="URL")
    parser.add_argument("--auth", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--mobile", action="store_true")
    parser.add_argument("--jpeg", action="store_true")
    parser.add_argument("--redact", action="store_true")
    parser.add_argument("--redact-selector", action="append", default=[], metavar="CSS")
    parser.add_argument("--redact-all", action="store_true")
    parser.add_argument("--keep-selector", action="append", default=[], metavar="CSS")
    parser.add_argument("--click-nav", action="append", default=[], metavar="TEXT")
    parser.add_argument("--wait", type=int, default=1500)
    parser.add_argument("-h", "--help", action="store_true")

    # parse_known_args + gop phan du: argparse voi nargs="*" khong chiu duoc co
    # dat xen giua cac URL (vi du "slug --jpeg url1 url2"). Gop lai cho de dung.
    args, leftover = parser.parse_known_args(argv[1:])
    args.urls += [item for item in leftover if not item.startswith("-")]

    if args.help:
        print(__doc__)
        return 0

    if args.login:
        run_login(args.slug, args.login)
        return 0

    if not args.urls:
        print("Loi: can it nhat mot URL. Xem huong dan bang --help.")
        return 1

    return capture(
        args.slug,
        args.urls,
        use_auth=args.auth,
        full_page=args.full,
        mobile=args.mobile,
        wait_ms=args.wait,
        jpeg=args.jpeg,
        redact=args.redact,
        redact_selectors=args.redact_selector,
        redact_all=args.redact_all,
        keep_selectors=args.keep_selector,
        click_nav=args.click_nav,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv))
