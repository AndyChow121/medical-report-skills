import json
import argparse
import os

TARGET_UNIQUE_PMIDS = 30
RECOMMENDED_BUFFER_PMIDS = 36

def count_references(filename="references.json"):
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to decode {filename}.")
        return

    unique_pmids = set()
    section_counts = {}

    for entry in data:
        pmid = entry.get('pmid')
        section = entry.get('section', 'Unknown')
        
        if pmid:
            unique_pmids.add(pmid)
        
        section_counts[section] = section_counts.get(section, 0) + 1

    total_unique = len(unique_pmids)
    
    print(f"\n--- Reference Statistics ---")
    print(f"Total Unique PMIDs: {total_unique}")
    print(f"Total Entries: {len(data)}")
    print(f"\n--- By Section ---")
    for section, count in section_counts.items():
        print(f"{section}: {count}")
    
    if total_unique < TARGET_UNIQUE_PMIDS:
        print(f"\n⚠️  Warning: Unique references ({total_unique}) are fewer than the minimum target of {TARGET_UNIQUE_PMIDS}.")
    elif total_unique < RECOMMENDED_BUFFER_PMIDS:
        print(f"\n✅ Minimum target reached: >= {TARGET_UNIQUE_PMIDS} unique references available.")
        print(f"建议再补充到 {RECOMMENDED_BUFFER_PMIDS} 篇左右，为正文改写和去重留出余量。")
    else:
        print(f"\n✅ Recommended target reached: >= {RECOMMENDED_BUFFER_PMIDS} unique references available.")

    print("\n" + "="*40)
    print("【状态机 (State Machine)】")
    print("当前状态: 阶段二 (Data Retrieval) - 检查文献数量完成。")
    print("下一步建议: ")
    if total_unique >= TARGET_UNIQUE_PMIDS:
        print(f"- 当前已达到快速交付下限（>= {TARGET_UNIQUE_PMIDS} 篇），可直接运行 `python scripts/read_references.py global_pool` 开始连续写作。")
        print(f"- 若希望降低后续改写风险，可继续补充到 {RECOMMENDED_BUFFER_PMIDS} 篇左右，但不再建议切回按章节慢检索。")
    else:
        print(f"- 当前未达到快速交付下限（{total_unique} < {TARGET_UNIQUE_PMIDS}），请继续使用 `build_topic_library.py` 补充主题总检索。")
        print("- 快速版默认先补强 `global_pool`，而不是拆回各章节分别联网。")
    print("="*40 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Count unique references in references.json")
    parser.add_argument("--file", default="references.json", help="Path to references.json file")
    args = parser.parse_args()
    
    count_references(args.file)

if __name__ == "__main__":
    main()
