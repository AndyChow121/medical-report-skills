import argparse
import json
import sys
import os

DEFAULT_REFERENCE_PREVIEW_LIMIT = 12
DEFAULT_ABSTRACT_PREVIEW_CHARS = 400
DEFAULT_SECTION_FILTER = "global_pool"
GLOBAL_SECTION_NAMES = {"global_pool", "master_library"}

def normalize_year(ref):
    year = str(ref.get("year", "0"))
    return int(year) if year.isdigit() else 0

def shorten_text(text, limit):
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."

def read_references(section_filter=None, file_path="references.json"):
    """
    Reads the references.json file and prints references matching the section filter.
    """
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found. Please ensure retrieval step is done.", file=sys.stderr)
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            references = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to decode {file_path}.", file=sys.stderr)
        return

    filtered_refs = []
    global_refs = []
    for ref in references:
        # If no filter, show all. If filter, check if section field contains the filter string (case-insensitive)
        current_section = ref.get("section", "").lower()
        if current_section in GLOBAL_SECTION_NAMES:
            global_refs.append(ref)
        if section_filter is None or section_filter.lower() in current_section:
            filtered_refs.append(ref)

    fallback_used = False
    if section_filter and not filtered_refs and global_refs:
        filtered_refs = list(global_refs)
        fallback_used = True

    filtered_refs.sort(key=normalize_year, reverse=True)
    total_count = len(filtered_refs)

    print(f"--- References for Section: '{section_filter if section_filter else 'ALL'}' ---")
    print(f"Matched references: {total_count}")
    if fallback_used:
        print("No section-specific references found. Fallback to topic-wide global pool.")

    if total_count == 0:
        print("No references found for this section.")
        return

    preview_refs = filtered_refs[:DEFAULT_REFERENCE_PREVIEW_LIMIT]
    for index, ref in enumerate(preview_refs, start=1):
        print(f"\n[Ref {index}]")
        print(f"Title: {ref.get('title', 'N/A')}")
        print(f"Year: {ref.get('year', 'N/A')}")
        print(f"PMID: {ref.get('pmid', 'N/A')}")
        print(f"Query: {ref.get('search_query', 'N/A')}")
        print(f"Abstract: {shorten_text(ref.get('abstract', 'N/A'), DEFAULT_ABSTRACT_PREVIEW_CHARS)}")

    hidden_count = total_count - len(preview_refs)
    if hidden_count > 0:
        print(f"\n... 另有 {hidden_count} 篇未展开显示，默认已省略长摘要以提升写作速度。")
        print("如确需查看全部原始摘要，请编辑脚本常量后再运行。")

def main():
    parser = argparse.ArgumentParser(description="Read references from JSON filtered by section.")
    parser.add_argument("section", nargs='?', default=DEFAULT_SECTION_FILTER, help="Section name to filter by (fuzzy match)")
    parser.add_argument("--file", default="references.json", help="Path to references.json")
    
    args = parser.parse_args()
    
    # Check if file exists in current or parent directory (standard agent context awareness)
    # The agent might run this from the root or the skill dir
    if os.path.exists(args.file):
        target_file = args.file
    elif os.path.exists(os.path.join("MedicalReviewSkill", args.file)):
        target_file = os.path.join("MedicalReviewSkill", args.file)
    else:
        # Fallback to current, will likely error if missing
        target_file = args.file
        
    read_references(args.section, target_file)

    print("\n" + "="*40)
    print("【状态机 (State Machine)】")
    print(f"当前状态: 阶段三 (分章撰写) - 已读取 `{args.section if args.section else DEFAULT_SECTION_FILTER}` 的精简文献视图。")
    print("下一步建议: ")
    print("- 开始基于上述标题、年份、检索式和摘要摘录撰写当前的 `[章节名].md` 文件，每个关键观点请加 `[PMID: xxx]` 标注。")
    print("- 若当前信息已经足够，请不要反复展开全部摘要，以免显著拖慢长文写作。")
    print("- 默认推荐直接复用 `global_pool` 总库连续写完整篇综述。")
    print("- 撰写完成后继续下一章节，或进入阶段四撰写结论 (conclusion.md) 和摘要(abstract.md)。")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
