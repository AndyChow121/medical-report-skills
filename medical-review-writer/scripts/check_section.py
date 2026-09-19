import argparse
import os
import re
import sys

MIN_SECTION_WORD_COUNT = 1200
MIN_SECTION_REFERENCES = 8

def count_words(text):
    # Process text for typical Chinese/English mixed content
    # Remove markdown tags typically
    text_clean = re.sub(r'[#*`_\[\]()]+', ' ', text)
    # Count chinese characters separately
    hanzi = re.findall(r'[\u4e00-\u9fff]', text_clean)
    # Count english words
    eng_words = re.findall(r'\b[a-zA-Z]+\b', text_clean)
    return len(hanzi) + len(eng_words)

def count_references(text):
    # Matches [PMID:xxx] or [PMID: xxx]
    pmid_pattern = re.compile(r'\[PMID:\s*(\d+)\]', re.IGNORECASE)
    all_matched_pmids = pmid_pattern.findall(text)
    unique_pmids = set(all_matched_pmids)
    return len(unique_pmids)

def check_reference_density(text):
    # Split text into sentences using common punctuation marks.
    sentences = re.split(r'[。！？.!?]+', text)
    violating_sentences = []
    pmid_pattern = re.compile(r'\[PMID:\s*\d+\]', re.IGNORECASE)
    
    for sentence in sentences:
        refs_in_sentence = pmid_pattern.findall(sentence)
        if len(refs_in_sentence) > 2:
            violating_sentences.append((sentence.strip()[:50] + "...", len(refs_in_sentence)))
    return violating_sentences

def main():
    parser = argparse.ArgumentParser(description="Check word count and reference count in a markdown file.")
    parser.add_argument("file", help="Path to the markdown file to check (e.g., section_1.md)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {args.file}: {e}", file=sys.stderr)
        sys.exit(1)

    word_count = count_words(content)
    ref_count = count_references(content)
    violating_sentences = check_reference_density(content)

    print(f"--- Document Check: {args.file} ---")
    print(f"Estimated Word/Char Count: {word_count}")
    print(f"Unique References (PMIDs): {ref_count}")
    
    if violating_sentences:
        print("\n[Warning] The following sentences have more than 2 citations:")
        for sentence, count in violating_sentences:
            print(f"  - ({count} refs) {sentence}")

    print("\n" + "="*40)
    print("【状态机 (State Machine)】")
    print(f"当前状态: 章节 `{os.path.basename(args.file)}` 质量检查完成。字数: {word_count}, 参考文献数: {ref_count}。")
    print("下一步建议: ")
    
    if ref_count < MIN_SECTION_REFERENCES:
        print(f"- 参考文献过少（{ref_count} < {MIN_SECTION_REFERENCES}），建议运行 `pubmed_search.py` 并附加 `--post-write` 参数补充检索该章节所需文献。")
    elif word_count < MIN_SECTION_WORD_COUNT:
        print(f"- ⚠️ 注意：当前章节字数不足（{word_count} < {MIN_SECTION_WORD_COUNT}字）。为支持整篇综述达到 5000 字以上，建议您进一步扩写该章节。")
        print("- 补充内容时如有必要，请继续检索支持文献。")
    elif violating_sentences:
        print(f"- ⚠️ 注意：发现 {len(violating_sentences)} 个句子引用了超过2篇文献！")
        print("- 强制要求：请修改上述过度引用的句子。将密集的引用分散到不同的子句中，或展开对引用的具体分析，确保每句话引用不超过2篇。")
        print("- 修改后请再次运行 `check_section.py` 进行检查。")
    else:
        print("- 当前章节已达到快速交付标准：参考文献数量、分布密度和章节规模均达标。")
        print("- 请用中文简要汇报该章节的完成情况、字数及参考文献数。")
        print("- 若用户未要求逐章确认，可直接继续下一章节，以保持 3 分钟内完成整篇综述的节奏。")
        print("- 若所有章节完成，进入阶段五运行 `merge_review.py`。")
        
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
