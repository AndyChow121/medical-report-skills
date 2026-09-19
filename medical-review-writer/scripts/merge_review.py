import os
import glob
import re
import argparse
import sys

TARGET_TOTAL_WORD_COUNT = 5000
TARGET_TOTAL_REFERENCES = 30

def natural_sort_key(s):
    """
    Sort strings containing numbers naturally, e.g. section_2.md comes before section_10.md
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def count_words(text):
    text_clean = re.sub(r'[#*`_\[\]()]+', ' ', text)
    hanzi = re.findall(r'[\u4e00-\u9fff]', text_clean)
    eng_words = re.findall(r'\b[a-zA-Z]+\b', text_clean)
    return len(hanzi) + len(eng_words)

def count_references(text):
    pmid_pattern = re.compile(r'\[PMID:\s*(\d+)\]', re.IGNORECASE)
    return len(set(pmid_pattern.findall(text)))

def merge_files(output_file, input_patterns):
    """
    Merges files matching the input patterns into a single Markdown file.
    """
    files_to_merge = []
    
    # Expand patterns preserving order
    for pattern in input_patterns:
        # Check if pattern contains wildcards
        if any(char in pattern for char in ['*', '?', '[']):
            matched = glob.glob(pattern)
            # Sort matched files naturally
            matched.sort(key=natural_sort_key)
            if not matched:
                print(f"Warning: No files found for pattern '{pattern}'", file=sys.stderr)
            files_to_merge.extend(matched)
        else:
            # Exact filename
            if os.path.exists(pattern):
                files_to_merge.append(pattern)
            else:
                 print(f"Error: File '{pattern}' not found.", file=sys.stderr)
                 sys.exit(1)

    # Remove duplicates while preserving order? 
    # Usually patterns might overlap? Let's assume user knows what they are doing or just unique them.
    # Uniquify:
    seen = set()
    unique_files = []
    for f in files_to_merge:
        if f not in seen:
            if os.path.basename(f).lower() == 'outline.md':
                print(f"Skipping {f} (outline file)", file=sys.stderr)
                continue
            unique_files.append(f)
            seen.add(f)
            
    if not unique_files:
        print("No files to merge. Please check your patterns.", file=sys.stderr)
        return

    print(f"Merging {len(unique_files)} files: {', '.join(unique_files)}", file=sys.stderr)

    content_parts = []
    for filepath in unique_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content_parts.append(f.read().strip())
        except Exception as e:
            print(f"Error reading {filepath}: {e}", file=sys.stderr)

    # Join with double newlines
    full_content = "\n\n".join(content_parts)
    
    total_word_count = count_words(full_content)
    total_reference_count = count_references(full_content)

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_content)
        print(f"Successfully merged files into '{output_file}'")
        print(f"Estimated total word/char count: {total_word_count}")
        print(f"Unique references in merged draft: {total_reference_count}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}", file=sys.stderr)

    return total_word_count, total_reference_count

def main():
    parser = argparse.ArgumentParser(description="Merge markdown files into a single document.")
    parser.add_argument("inputs", nargs="*", 
                        help="Input files or patterns (e.g. 'abstract.md' 'section_*.md'). If empty, uses default preset.")
    parser.add_argument("-o", "--output", default="Review_Final.md", 
                        help="Output filename (default: Review_Final.md)")
    
    args = parser.parse_args()
    
    inputs = args.inputs
    if not inputs:
        # Default behavior if no args provided: Smart Default
        inputs = ["abstract.md", "introduction.md", "section_*.md", "conclusion.md"]
        print("No input files specified. Using default pattern: " + " ".join(inputs), file=sys.stderr)
    
    total_word_count, total_reference_count = merge_files(args.output, inputs)

    if total_word_count is None or total_reference_count is None:
        print("合并未成功完成，无法生成后续状态建议。", file=sys.stderr)
        sys.exit(1)

    print("\n" + "="*40)
    print("【状态机 (State Machine)】")
    print("当前状态: 阶段五 (摘要与定稿) - 章节文件已合并为最终草稿。")
    print("下一步建议: ")
    if total_word_count < TARGET_TOTAL_WORD_COUNT:
        print(f"- 当前总字数不足（{total_word_count} < {TARGET_TOTAL_WORD_COUNT}），请优先扩写前言或正文后再格式化引用。")
    elif total_reference_count < TARGET_TOTAL_REFERENCES:
        print(f"- 当前总参考文献不足（{total_reference_count} < {TARGET_TOTAL_REFERENCES}），请先补充检索和引用后再格式化。")
    else:
        print("- 当前总字数和总参考文献数均已达到快速交付要求。")
        print("- 请检查合并后的文档排版与内容，若无误，进入阶段六运行 `format_citations.py`。")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
