#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert react-native-interview-middle.md to a formatted .docx Word file.
Adds Vietnamese explanation notes for advanced technical terms on first appearance.
"""

import re
import os
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── File paths ──────────────────────────────────────────────────────────────
INPUT_FILE  = r"c:\Users\ALLIANCEITSC\Documents\learning\react-native-interview-middle.md"
OUTPUT_FILE = r"c:\Users\ALLIANCEITSC\Documents\learning\react-native-interview-middle.docx"

# ── Color constants ──────────────────────────────────────────────────────────
DARK_BLUE  = RGBColor(0x00, 0x33, 0x66)
DARK_RED   = RGBColor(0xCC, 0x00, 0x00)
GREEN_NOTE = RGBColor(0x00, 0x80, 0x00)
CODE_BG    = "F0F0F0"

# ── Advanced term explanations (Vietnamese) ──────────────────────────────────
EXPLANATIONS = {
    "Event Loop":
        "Cơ chế JS kiểm tra và thực thi các tác vụ từ Call Stack và Queue theo vòng lặp liên tục.",
    "Microtask Queue":
        "Hàng đợi ưu tiên cao, chứa callback của Promise.then(), chạy TRƯỚC Macrotask Queue.",
    "Macrotask Queue":
        "Hàng đợi thông thường, chứa callback của setTimeout, setInterval, I/O.",
    "Closure":
        "Hàm \"nhớ\" biến trong scope bên ngoài dù scope đó đã kết thúc.",
    "Prototype Chain":
        "Cơ chế kế thừa trong JS: khi không tìm thấy property trên object, JS tự động tìm lên object cha (prototype).",
    "JSI":
        "Cầu nối mới trong React Native Architecture mới, cho phép JS gọi native code trực tiếp không qua JSON bridge.",
    "Hermes":
        "JavaScript engine được tối ưu riêng cho React Native, giúp app khởi động nhanh hơn và dùng ít RAM hơn.",
    "Reanimated":
        "Thư viện animation chạy hoàn toàn trên UI thread (không qua JS bridge), cho animation mượt 60fps.",
    "TurboModules":
        "Hệ thống Native Modules mới trong kiến trúc mới của React Native, lazy-load và nhanh hơn.",
    "Fabric":
        "Renderer mới của React Native, xử lý UI trực tiếp trên C++ thay vì qua bridge.",
    "Metro bundler":
        "Công cụ đóng gói (bundler) JavaScript dành riêng cho React Native.",
    "RTK Query":
        "Công cụ data fetching tích hợp trong Redux Toolkit, tự động cache và refetch.",
    "Immer":
        "Thư viện cho phép \"mutate\" state trực tiếp trong Redux Toolkit nhưng thực ra tạo bản copy mới (immutable).",
    "stale closure":
        "Closure bị \"cũ\" khi hàm trong useEffect đóng lấy giá trị state/prop tại thời điểm tạo, không cập nhật khi re-render.",
    "debounce":
        "Kỹ thuật trì hoãn thực thi hàm cho đến khi ngừng gọi trong một khoảng thời gian nhất định.",
    "FlatList virtualization":
        "Kỹ thuật chỉ render các item đang hiển thị trên màn hình, giải phóng bộ nhớ cho các item ngoài viewport.",
    "InteractionManager":
        "API của React Native cho phép trì hoãn tác vụ nặng sau khi animation/transition hoàn thành.",
    "Error Boundary":
        "Component React bắt lỗi JavaScript trong cây con và hiển thị UI fallback thay vì crash app.",
    "AsyncStorage":
        "Bộ nhớ key-value bất đồng bộ, lưu trữ dữ liệu đơn giản trên thiết bị (tương tự localStorage).",
}

# Aliases: if canonical key not found literally, match these patterns instead
TERM_ALIASES = {
    "Prototype Chain": [
        re.compile(r'Prototype\s*[&]\s*this', re.IGNORECASE),
        re.compile(r'Prototype\s+Chain', re.IGNORECASE),
        re.compile(r'\bPrototype\b', re.IGNORECASE),
    ],
    "FlatList virtualization": [
        re.compile(r'FlatList\s+virtualization', re.IGNORECASE),
        re.compile(r'virtualization', re.IGNORECASE),
        re.compile(r'FlatList.*optim', re.IGNORECASE),
    ],
    "debounce": [
        re.compile(r'\bdebounce\b', re.IGNORECASE),
        re.compile(r'useDebounce', re.IGNORECASE),
    ],
    "stale closure": [
        re.compile(r'stale\s+closure', re.IGNORECASE),
        re.compile(r'stale closure', re.IGNORECASE),
    ],
    "Immer": [
        re.compile(r'\bImmer\b', re.IGNORECASE),
    ],
    "InteractionManager": [
        re.compile(r'\bInteractionManager\b', re.IGNORECASE),
    ],
}

# Build sorted list: longer/more-specific terms first
SORTED_TERMS = sorted(EXPLANATIONS.keys(), key=lambda t: -len(t))
explained_terms: set = set()   # track which have been explained


# ═══════════════════════════════════════════════════════════════════════════════
#  XML / style helpers
# ═══════════════════════════════════════════════════════════════════════════════

def set_para_shading(paragraph, fill_hex: str):
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  fill_hex)
    pPr.append(shd)


def set_para_border_top(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    top = OxmlElement('w:top')
    top.set(qn('w:val'),   'single')
    top.set(qn('w:sz'),    '6')
    top.set(qn('w:space'), '1')
    top.set(qn('w:color'), '003366')
    pBdr.append(top)
    pPr.append(pBdr)


def add_explanation_paragraph(doc: Document, term: str):
    explanation = EXPLANATIONS[term]
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.8)
    p.paragraph_format.right_indent = Cm(0.5)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(5)
    run = p.add_run(f"💡 Giải thích: {explanation}")
    run.italic = True
    run.font.size = Pt(10)
    run.font.color.rgb = GREEN_NOTE
    run.font.name = 'Calibri'
    return p


def _term_found_in(text: str, term: str) -> bool:
    """Return True if *term* (or its alias patterns) appear in *text*."""
    # Direct match first
    if re.search(re.escape(term), text, re.IGNORECASE):
        return True
    # Alias match
    if term in TERM_ALIASES:
        for pat in TERM_ALIASES[term]:
            if pat.search(text):
                return True
    return False


def check_and_explain(doc: Document, text: str, also_in_code: bool = False):
    """
    Check *text* for unexlained terms; add explanation notes to *doc*.
    *also_in_code*: if True, code-block content is also considered.
    """
    for term in SORTED_TERMS:
        if term in explained_terms:
            continue
        if _term_found_in(text, term):
            explained_terms.add(term)
            add_explanation_paragraph(doc, term)


# ═══════════════════════════════════════════════════════════════════════════════
#  Document setup
# ═══════════════════════════════════════════════════════════════════════════════

def setup_document() -> Document:
    doc = Document()
    for section in doc.sections:
        section.top_margin    = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin   = Cm(2)
        section.right_margin  = Cm(2)
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    style.paragraph_format.space_after  = Pt(4)
    style.paragraph_format.space_before = Pt(0)
    return doc


# ═══════════════════════════════════════════════════════════════════════════════
#  Inline text parser — handles **bold** and `code` within a text string
# ═══════════════════════════════════════════════════════════════════════════════

def add_inline_runs(paragraph, text: str, base_size: int = 11,
                    base_color: RGBColor = None, base_bold: bool = False,
                    base_italic: bool = False):
    """
    Parse *text* for **bold** and `inline code` segments and add runs
    to *paragraph* accordingly.
    """
    # Split on inline code first
    segs = re.split(r'(`[^`]+`)', text)
    for seg in segs:
        cm = re.match(r'^`([^`]+)`$', seg)
        if cm:
            run = paragraph.add_run(cm.group(1))
            run.font.name = 'Courier New'
            run.font.size = Pt(9)
            if base_color:
                run.font.color.rgb = base_color
        else:
            # Handle **bold**
            bold_segs = re.split(r'(\*\*[^*]+\*\*)', seg)
            for bp in bold_segs:
                bm = re.match(r'^\*\*([^*]+)\*\*$', bp)
                if bm:
                    run = paragraph.add_run(bm.group(1))
                    run.bold = True
                    run.font.size = Pt(base_size)
                    run.font.name = 'Calibri'
                    if base_color:
                        run.font.color.rgb = base_color
                    if base_italic:
                        run.italic = True
                else:
                    if bp:
                        run = paragraph.add_run(bp)
                        run.bold = base_bold
                        run.italic = base_italic
                        run.font.size = Pt(base_size)
                        run.font.name = 'Calibri'
                        if base_color:
                            run.font.color.rgb = base_color


# ═══════════════════════════════════════════════════════════════════════════════
#  Paragraph adders
# ═══════════════════════════════════════════════════════════════════════════════

def add_h1(doc: Document, text: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(12)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = DARK_BLUE
    run.font.name = 'Calibri'
    check_and_explain(doc, text)


def add_h2(doc: Document, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(6)
    set_para_border_top(p)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = DARK_BLUE
    run.font.name = 'Calibri'
    check_and_explain(doc, text)


def add_h3(doc: Document, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.3)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(13)
    run.font.color.rgb = DARK_BLUE
    run.font.name = 'Calibri'
    check_and_explain(doc, text)


def add_h4(doc: Document, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.5)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(12)
    run.font.color.rgb = DARK_BLUE
    run.font.name = 'Calibri'
    check_and_explain(doc, text)


def add_normal(doc: Document, text: str, indent: float = 0):
    """Normal paragraph with **bold** and `inline code` support."""
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(4)
    add_inline_runs(p, text, base_size=11)
    check_and_explain(doc, text)


def add_question(doc: Document, text: str):
    """Bold dark-red Q: paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(4)
    # Strip outer ** if the whole line is bold
    inner = re.sub(r'^\*\*(.+)\*\*\s*$', r'\1', text.strip())
    add_inline_runs(p, inner, base_size=11, base_color=DARK_RED, base_bold=True)
    check_and_explain(doc, text)


def add_code_block(doc: Document, lines: list):
    """Gray-background Courier New code block — also checks for terms."""
    full_text = '\n'.join(lines)
    for line in lines:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent  = Cm(0.6)
        p.paragraph_format.right_indent = Cm(0.3)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after  = Pt(0)
        set_para_shading(p, CODE_BG)
        run = p.add_run(line if line else ' ')
        run.font.name = 'Courier New'
        run.font.size = Pt(9)
    # Check the whole code block text for terms (explain AFTER the block)
    check_and_explain(doc, full_text, also_in_code=True)


def add_bullet(doc: Document, text: str, level: int = 0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent  = Cm(0.5 + level * 0.5)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(2)
    add_inline_runs(p, text, base_size=11)
    check_and_explain(doc, text)


def add_numbered(doc: Document, text: str, level: int = 0):
    p = doc.add_paragraph(style='List Number')
    p.paragraph_format.left_indent  = Cm(0.5 + level * 0.5)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(2)
    add_inline_runs(p, text, base_size=11)
    check_and_explain(doc, text)


def add_table_row(doc: Document, text: str):
    cleaned = text.strip().strip('|')
    cols = [c.strip() for c in cleaned.split('|')]
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.4)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(1)
    first = True
    for col in cols:
        if not col or re.match(r'^[-:]+$', col):
            continue
        if not first:
            sep = p.add_run('   │   ')
            sep.font.size = Pt(11)
        add_inline_runs(p, col, base_size=11)
        first = False
    check_and_explain(doc, text)


def add_hr(doc: Document):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'),   'single')
    bottom.set(qn('w:sz'),    '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'AAAAAA')
    pBdr.append(bottom)
    pPr.append(pBdr)


# ═══════════════════════════════════════════════════════════════════════════════
#  Markdown parser
# ═══════════════════════════════════════════════════════════════════════════════

def is_table_separator(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith('|'):
        return False
    inner = stripped.strip('|')
    cols = inner.split('|')
    return all(re.match(r'^\s*:?-+:?\s*$', c) for c in cols if c.strip())


def parse_and_convert(md_text: str, doc: Document):
    lines = md_text.splitlines()
    i = 0
    in_code_block = False
    code_lines: list = []

    while i < len(lines):
        line = lines[i]

        # ── Code block toggle ──────────────────────────────────────────────
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lines = []
                i += 1
                continue
            else:
                add_code_block(doc, code_lines)
                # Small spacer after code block
                sp = doc.add_paragraph()
                sp.paragraph_format.space_after = Pt(2)
                in_code_block = False
                code_lines = []
                i += 1
                continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # ── Horizontal rule ────────────────────────────────────────────────
        if re.match(r'^---+\s*$', line.strip()):
            add_hr(doc)
            i += 1
            continue

        # ── Headings ───────────────────────────────────────────────────────
        if re.match(r'^# [^#]', line):
            add_h1(doc, line[2:].strip())
            i += 1
            continue

        if re.match(r'^## [^#]', line):
            add_h2(doc, line[3:].strip())
            i += 1
            continue

        if re.match(r'^### [^#]', line):
            add_h3(doc, line[4:].strip())
            i += 1
            continue

        if re.match(r'^#### ', line):
            add_h4(doc, line[5:].strip())
            i += 1
            continue

        # ── Table separator — skip ─────────────────────────────────────────
        if is_table_separator(line):
            i += 1
            continue

        # ── Table row ─────────────────────────────────────────────────────
        if line.strip().startswith('|') and '|' in line.strip()[1:]:
            add_table_row(doc, line)
            i += 1
            continue

        # ── Checkbox list ─────────────────────────────────────────────────
        check_match = re.match(r'^\s*-\s+\[([ x])\]\s+(.*)', line)
        if check_match:
            checked = check_match.group(1) == 'x'
            content = check_match.group(2).strip()
            prefix = '☑ ' if checked else '☐ '
            add_bullet(doc, prefix + content, 0)
            i += 1
            continue

        # ── Bullet list ───────────────────────────────────────────────────
        bullet_match = re.match(r'^(\s*)[-*+]\s+(.*)', line)
        if bullet_match:
            level = len(bullet_match.group(1)) // 2
            add_bullet(doc, bullet_match.group(2).strip(), level)
            i += 1
            continue

        # ── Numbered list ─────────────────────────────────────────────────
        num_match = re.match(r'^(\s*)(\d+)\.\s+(.*)', line)
        if num_match:
            level = len(num_match.group(1)) // 2
            add_numbered(doc, num_match.group(3).strip(), level)
            i += 1
            continue

        # ── Empty line ────────────────────────────────────────────────────
        if line.strip() == '':
            sp = doc.add_paragraph()
            sp.paragraph_format.space_after = Pt(1)
            i += 1
            continue

        # ── Arrow lines ───────────────────────────────────────────────────
        if line.strip().startswith('→'):
            add_normal(doc, line.strip(), indent=0.5)
            i += 1
            continue

        # ── Q: question bold lines ────────────────────────────────────────
        if re.match(r'^\*\*Q:', line.strip()):
            add_question(doc, line.strip())
            i += 1
            continue

        # ── Default normal paragraph ──────────────────────────────────────
        add_normal(doc, line.strip())
        i += 1

    # Close any unclosed code block
    if in_code_block and code_lines:
        add_code_block(doc, code_lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"Reading: {INPUT_FILE}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        md_text = f.read()
    print(f"  → {len(md_text):,} chars, {len(md_text.splitlines())} lines")

    print("Setting up document...")
    doc = setup_document()

    print("Parsing and converting markdown...")
    parse_and_convert(md_text, doc)

    print(f"\nTerms explained ({len(explained_terms)}):")
    for t in sorted(explained_terms):
        print(f"  ✓ {t}")

    not_found = set(EXPLANATIONS.keys()) - explained_terms
    if not_found:
        print(f"\n  ⚠ Terms NOT found/explained: {sorted(not_found)}")
    else:
        print("\n  ✓ All terms explained!")

    print(f"\nSaving to: {OUTPUT_FILE}")
    doc.save(OUTPUT_FILE)
    print("  ✓ Saved!")

    size = os.path.getsize(OUTPUT_FILE)
    print(f"  File size: {size:,} bytes ({size/1024:.1f} KB)")


if __name__ == '__main__':
    main()
