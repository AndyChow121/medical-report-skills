import argparse
import sys

from pubmed_search import fetch_details, save_to_json, search_pubmed

DEFAULT_TOPIC_LIBRARY_MAX = 60
DEFAULT_TOPIC_LIBRARY_SECTION = "global_pool"
MIN_TOPIC_LIBRARY_TARGET = 30


def main():
    parser = argparse.ArgumentParser(description="Build a single topic-wide literature pool for fast review writing.")
    parser.add_argument("topic", help="Review topic or PubMed query")
    parser.add_argument("--max", type=int, default=DEFAULT_TOPIC_LIBRARY_MAX, help="Max results to retrieve")
    parser.add_argument("--file", default="references.json", help="Output JSON file")
    args = parser.parse_args()

    print(f"Building topic-wide literature pool for: {args.topic}", file=sys.stderr)
    id_list = search_pubmed(args.topic, args.max)

    if not id_list:
        print("No results found.", file=sys.stderr)
        sys.exit(1)

    papers = fetch_details(id_list)
    added = save_to_json(papers, DEFAULT_TOPIC_LIBRARY_SECTION, args.topic, args.file)

    print(f"Successfully fetched {len(papers)} papers.")
    print(f"Added {added} new unique papers to {args.file} under section '{DEFAULT_TOPIC_LIBRARY_SECTION}'.")

    for paper in papers[:5]:
        print(f"- {paper.get('title')} ({paper.get('year')}) [PMID: {paper.get('pmid')}]")

    print("\n" + "=" * 40)
    print("【状态机 (State Machine)】")
    print("当前状态: 阶段二 (Data Retrieval) - 已按主题完成一次性总库检索。")
    print("下一步建议: ")
    if len(papers) < MIN_TOPIC_LIBRARY_TARGET:
        print(f"- 当前有效文献偏少（{len(papers)} < {MIN_TOPIC_LIBRARY_TARGET}），建议优化主题检索词后再补 1 次总库检索。")
    else:
        print("- 当前总库规模已适合进入快速写作。")
    print("- 运行 `python scripts/count_references.py` 检查总 PMID 数量。")
    print("- 后续撰写各章节时，直接运行 `python scripts/read_references.py global_pool` 复用整库文献。")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    main()
