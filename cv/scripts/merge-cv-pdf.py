r"""Tu dong render cac trang CV (HTML) thanh PDF roi ghep thanh 1 file gui HR.

Khong can Ctrl+P thu cong nua:
  1. Chi ra danh sach file HTML (va/hoac PDF co san) theo dung thu tu muon xuat hien.
  2. Script tu dung Chrome/Edge headless de "in" tung trang HTML thanh PDF
     (giu nguyen CSS @media print cua site, vi du an cac nut/nav .no-print).
  3. Ghep tat ca PDF (vua render + PDF co san neu co) thanh 1 file.

Can cai pypdf truoc: python -m pip install pypdf

Chay:
  python cv/scripts/merge-cv-pdf.py cv/index.html cv/projects/hv-quan-ly-tai-san.html cv/projects/coshare.html -o cv-for-hr.pdf

Neu may khong co Chrome/Edge o duong dan mac dinh, chi ro bang --browser:
  python cv/scripts/merge-cv-pdf.py cv/index.html -o cv.pdf --browser "D:\Chrome\chrome.exe"
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfWriter

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_browser(explicit):
    if explicit:
        return explicit
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    found = shutil.which("chrome") or shutil.which("msedge") or shutil.which("google-chrome")
    if found:
        return found
    sys.exit("Khong tim thay Chrome/Edge o duong dan mac dinh. Dung --browser de chi duong dan thu cong.")


def render_html_to_pdf(browser, html_path, out_pdf):
    url = html_path.resolve().as_uri()
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={out_pdf}",
        "--virtual-time-budget=5000",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not out_pdf.exists():
        sys.exit(f"Render that bai cho {html_path}:\n{result.stderr}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "inputs",
        nargs="+",
        help="cac file .html (se tu render) hoac .pdf (dung truc tiep), dung thu tu can ghep",
    )
    ap.add_argument("-o", "--out", default="cv-for-hr.pdf", help="file PDF ket qua")
    ap.add_argument("--browser", help="duong dan chrome.exe / msedge.exe (tu dong do neu bo trong)")
    args = ap.parse_args()

    browser = None
    writer = PdfWriter()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for i, raw_path in enumerate(args.inputs):
            path = Path(raw_path)
            if not path.exists():
                sys.exit(f"Khong tim thay file: {path}")

            if path.suffix.lower() == ".pdf":
                writer.append(str(path))
                continue

            if browser is None:
                browser = find_browser(args.browser)

            out_pdf = tmp_dir / f"page-{i:02d}.pdf"
            print(f"Dang render {path.name} ...")
            render_html_to_pdf(browser, path, out_pdf)
            writer.append(str(out_pdf))

        with open(args.out, "wb") as f:
            writer.write(f)

    print(f"Da ghep {len(args.inputs)} file -> {args.out}")


if __name__ == "__main__":
    main()
