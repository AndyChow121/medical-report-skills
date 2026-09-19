import re
import sys
import argparse
import os

def revert_citations(file_path: str, inplace: bool = False, output_path: str = None):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        return

    # 1. Replace [[number]](https://pubmed.ncbi.nlm.nih.gov/pmid/) with [PMID: pmid]
    pattern = re.compile(r'\[\[\d+\]\]\(https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)/\)')
    new_content = pattern.sub(r'[PMID: \1]', content)

    # 2. Remove the ### References section
    if '### References' in new_content:
        new_content = new_content.split('### References')[0].rstrip() + '\n'

    if inplace:
        output_file = file_path
    elif output_path:
        output_file = output_path
    else:
        # Default behavior: print to standard output
        print(new_content)
        return

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Successfully reverted citations and saved to {output_file}")
    
    unique_pmids = set(re.findall(r'\[PMID:\s*\d+\]', new_content, re.IGNORECASE))
    return len(unique_pmids)

def main():
    parser = argparse.ArgumentParser(description="Revert formatted citations back to [PMID: xxx] format.")
    parser.add_argument("file", help="Path to formatted Markdown file")
    parser.add_argument("-i", "--inplace", action="store_true", help="Modify file in-place")
    parser.add_argument("-o", "--output", help="Path to output file")
    
    args = parser.parse_args()
    pmid_count = revert_citations(args.file, args.inplace, args.output)

    if pmid_count is None:
        return

    print("\n" + "="*40)
    print("【状态机 (State Machine)】")
    print(f"当前状态: 内容修改阶段 - 引用回退完成，提取到 {pmid_count} 篇独特参考文献。")
    print("下一步建议: ")
    if pmid_count < 30:
        print("- ⚠️ 注意：当前综述总参考文献数量偏少（不足30篇）。建议您针对薄弱段落，带 `--post-write` 或直接使用 `python scripts/pubmed_search.py` 补充检索新的参考文献。")
    else:
        print("- 当前综述参考文献总数达标。但如果在修改/扩写时发现特定观点论据不足，仍可随时使用 `python scripts/pubmed_search.py` 进行局部补充检索。")
    print("- 请基于该回退后的版本进行内容的修改或补充。")
    print("- 请牢记：补充新论据时依然使用 `[PMID: xxx]` 格式。")
    print("- 修改完毕且确认无误后，请重新运行 `python scripts/format_citations.py` 将其格式化为最终发布版。")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
