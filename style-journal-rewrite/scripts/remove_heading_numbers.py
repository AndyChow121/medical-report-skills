#!/usr/bin/env python3
"""
去除 DOCX 中所有标题的编号前缀。
匹配 '1. 标题' '1.1 子标题' '2. ' 等格式。
在原 run 文本上直接修改，不破坏段落结构。

用法：
    python remove_heading_numbers.py <输入.docx> [输出.docx]
    未指定输出文件时，覆盖保存到输入文件。
"""
import re
import sys
from docx import Document


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    src = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else src

    doc = Document(src)
    count = 0
    for para in doc.paragraphs:
        if not para.style.name.startswith("Heading"):
            continue
        old = para.text
        new = re.sub(r"^[\d\.]+\s+", "", old)
        if new == old or not para.runs:
            continue
        first = para.runs[0]
        cut = len(old) - len(new)
        if len(first.text) >= cut and first.text[:cut] == old[:cut]:
            first.text = first.text[cut:]
        else:
            first.text = new
        count += 1

    doc.save(output)
    print(f"已去除 {count} 个标题编号: {output}")


if __name__ == "__main__":
    main()
