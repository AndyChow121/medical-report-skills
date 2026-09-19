#!/usr/bin/env python3
"""
转换 DOCX 中参考文献编号样式。

支持三种场景：
  1. 纯文本编号：[N] ↔ N.（文末列表 + 文内引文同步改）
  2. Unicode 上标：[N] → 上标字符（如 ¹²³），组合规则可配置
  3. 字体上标：[N] → 字体格式 superscript（run.font.superscript=True）

参数说明（必须从参考文章的实际书写方式提取，不准假设）：
  --ref-list-style    文末列表编号样式: bracket|period|keep
  --style             文内引文样式: keep|unicode|font
  --range-joiner      连续引用范围连接符（参考文章写 ¹⁻³ 则用 --range-joiner ⁻）
  --group-separator   非连续引用分隔符（参考文章写 ¹,³ 则用 --group-separator ,）

用法示例：
  # [N] → N.（纯文本）
  python convert_ref_format.py --ref-list-style period --style keep 输入.docx 输出.docx

  # [N] → Unicode上标，连续合并，非连续逗号
  python convert_ref_format.py --ref-list-style keep --style unicode --range-joiner ⁻ --group-separator , 输入.docx 输出.docx

  # [N] → 字体上标，不合并
  python convert_ref_format.py --ref-list-style keep --style font 输入.docx 输出.docx
"""
import argparse
import re
import sys
from copy import deepcopy

from docx import Document
from docx.oxml.ns import qn

# Unicode superscript mapping
SUP = {
    "0": "\u2070", "1": "\u00B9", "2": "\u00B2", "3": "\u00B3",
    "4": "\u2074", "5": "\u2075", "6": "\u2076", "7": "\u2077",
    "8": "\u2078", "9": "\u2079",
}


# ==================== Helpers ====================

def to_sup(n):
    return "".join(SUP[c] for c in str(n))


def _parse_citation_groups(text):
    """将正文中 [N][N+1]... 分组为数字列表"""
    pat = r"\[(\d+)\]"
    matches = list(re.finditer(pat, text))
    if not matches:
        return text, []
    return text, matches


# ==================== Style: bracket ↔ period ====================

def _convert_ref_list_bracket_to_period(doc):
    """文末 [N] → N."""
    count, ref_start = 0, False
    for para in doc.paragraphs:
        t = para.text.strip()
        if "参考文献" in t and para.style.name.startswith("Heading"):
            ref_start = True
            continue
        if ref_start and t and para.runs:
            m = re.match(r"^\[(\d+)\](.*)", para.runs[0].text)
            if m:
                para.runs[0].text = f"{m.group(1)}. {m.group(2)}"
                count += 1
    return count


def _convert_ref_list_period_to_bracket(doc):
    """文末 N. → [N]"""
    count, ref_start = 0, False
    for para in doc.paragraphs:
        t = para.text.strip()
        if "参考文献" in t and para.style.name.startswith("Heading"):
            ref_start = True
            continue
        if ref_start and t and para.runs:
            m = re.match(r"^(\d+)\.\s*(.*)", para.runs[0].text)
            if m:
                para.runs[0].text = f"[{m.group(1)}] {m.group(2)}"
                count += 1
    return count


# ==================== Style: superscript (unicode) ====================

def _convert_inline_to_unicode_sup(text, range_joiner, group_separator):
    """将正文中的 [N] 组合转为 Unicode 上标"""
    text, matches = _parse_citation_groups(text)
    if not matches:
        return text

    result, last_end, i = [], 0, 0
    while i < len(matches):
        result.append(text[last_end : matches[i].start()])
        nums = [int(matches[i].group(1))]
        j = i + 1
        while j < len(matches) and matches[j].start() == matches[j - 1].end():
            nums.append(int(matches[j].group(1)))
            j += 1

        if len(nums) == 1:
            result.append(to_sup(nums[0]))
        elif range_joiner is not None and all(
            nums[k + 1] - nums[k] == 1 for k in range(len(nums) - 1)
        ):
            result.append(to_sup(nums[0]) + range_joiner + to_sup(nums[-1]))
        elif group_separator is not None:
            result.append(group_separator.join(to_sup(n) for n in nums))
        else:
            result.append("".join(to_sup(n) for n in nums))

        i, last_end = j, matches[j - 1].end()
    result.append(text[last_end:])
    return "".join(result)


def _apply_unicode_superscript(doc, range_joiner, group_separator):
    """全文遍历，替换引文为 Unicode 上标"""
    ref_start = False
    count = 0
    for para in doc.paragraphs:
        t = para.text.strip()
        if "参考文献" in t and para.style.name.startswith("Heading"):
            ref_start = True
        if ref_start:
            continue
        new_text = _convert_inline_to_unicode_sup(para.text, range_joiner, group_separator)
        if new_text != para.text:
            # 清空段落所有XML内容，保留段落属性
            # 注意：不能只靠 run.text = "" 来清空，因为 DOCX XML 中可能含有
            # 不在 para.runs 中的隐藏 w:t 节点，run.text 清除不掉它们
            pPr = para._element.find(qn("w:pPr"))
            pPr_copy = deepcopy(pPr) if pPr is not None else None
            para._element.clear()
            if pPr_copy is not None:
                para._element.append(pPr_copy)
            # 添加新 run
            from docx.oxml import OxmlElement
            new_r = OxmlElement("w:r")
            new_t = OxmlElement("w:t")
            new_t.text = new_text
            new_t.set(qn("xml:space"), "preserve")
            new_r.append(new_t)
            para._element.append(new_r)
            count += 1
    return count


# ==================== Style: superscript (font) ====================

def _split_run_for_superscript(run):
    """将带 [N] 的 run 拆成多个 run，引用部分设为上标。
    返回是否做了拆分。"""
    text = run.text
    if "[" not in text or "]" not in text:
        return False
    parts = re.split(r"(\[\d+\])", text)
    if len(parts) <= 1:
        return False

    parent = run._element.getparent()
    for part in parts:
        new_run = deepcopy(run)
        new_run.text = part
        rPr = new_run.find(qn("w:rPr"))
        if rPr is None:
            rPr = deepcopy(new_run.makeelement(qn("w:rPr"), {}))
            new_run.insert(0, rPr)
        if re.match(r"^\[\d+\]$", part):
            vertAlign = rPr.find(qn("w:vertAlign"))
            if vertAlign is None:
                vertAlign = deepcopy(rPr.makeelement(qn("w:vertAlign"), {}))
                rPr.append(vertAlign)
            vertAlign.set(qn("w:val"), "superscript")
        else:
            va = rPr.find(qn("w:vertAlign"))
            if va is not None:
                rPr.remove(va)
        run._element.addprevious(new_run)
    parent.remove(run._element)
    return True


def _apply_font_superscript(doc):
    """全文遍历，将 [N] 引文 run 拆分为字体上标"""
    ref_start = False
    count = 0
    for para in doc.paragraphs:
        t = para.text.strip()
        if "参考文献" in t and para.style.name.startswith("Heading"):
            ref_start = True
        if ref_start:
            continue
        for run in list(para.runs):
            if _split_run_for_superscript(run):
                count += 1
    return count


# ==================== Main ====================


def main():
    parser = argparse.ArgumentParser(
        description="转换 DOCX 参考文献编号样式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", help="输入 .docx 文件路径")
    parser.add_argument("output", nargs="?", help="输出 .docx 文件路径（默认覆盖输入）")
    parser.add_argument(
        "--ref-list-style",
        choices=["keep", "bracket", "period"],
        default="keep",
        help="文末列表编号样式: keep(不改), bracket([N]), period(N.)",
    )
    parser.add_argument(
        "--style",
        choices=["keep", "unicode", "font"],
        default="keep",
        help="文内引文样式: keep(不改), unicode(Unicode上标), font(字体上标)",
    )
    parser.add_argument("--range-joiner", default=None, help="连续引用范围连接符")
    parser.add_argument("--group-separator", default=None, help="非连续引用分隔符")

    args = parser.parse_args()
    src, output = args.input, args.output or args.input

    doc = Document(src)
    summary = []

    # 1) 文末列表编号
    if args.ref_list_style == "period":
        c = _convert_ref_list_bracket_to_period(doc)
        summary.append(f"文末列表: [N]→N. ({c}条)")
    elif args.ref_list_style == "bracket":
        c = _convert_ref_list_period_to_bracket(doc)
        summary.append(f"文末列表: N.→[N] ({c}条)")

    # 2) 文内引文
    if args.style == "unicode":
        if args.range_joiner is None and args.group_separator is None:
            print("警告: --style unicode 但未指定 --range-joiner 或 --group-separator，将使用 fallback 连写")
        c = _apply_unicode_superscript(doc, args.range_joiner, args.group_separator)
        summary.append(f"文内引文: →Unicode上标 ({c}段落)")
    elif args.style == "font":
        c = _apply_font_superscript(doc)
        summary.append(f"文内引文: →字体上标 ({c}个run拆分)")

    doc.save(output)
    print("转换完成。")
    for line in summary:
        print(f"  - {line}")
    print(f"输出文件: {output}")


if __name__ == "__main__":
    main()
