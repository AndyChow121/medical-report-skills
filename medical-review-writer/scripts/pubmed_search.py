import argparse
import sys
import json
import time
import os
import urllib.request
import urllib.parse
import re

# Base URLs for NCBI Entrez E-utilities
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
DEFAULT_MAX_RESULTS = 12
REQUEST_PAUSE_SECONDS = 0.34
FETCH_BATCH_SIZE = 100
ALLOWED_SECTION_PATTERN = r'^(introduction|section_\d+|global_pool|master_library)$'

def search_pubmed(query, max_results=20):
    """
    Search PubMed for a given query and return a list of IDs.
    """
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "date" # Get most recent
    }
    
    query_string = urllib.parse.urlencode(params)
    url = f"{ESEARCH_URL}?{query_string}"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            id_list = data.get("esearchresult", {}).get("idlist", [])
            return id_list
    except Exception as e:
        print(f"Error searching PubMed: {e}", file=sys.stderr)
        return []

def fetch_details(id_list):
    """
    Fetch summary metadata for a list of PubMed IDs using esummary JSON.
    """
    if not id_list:
        return []

    papers = []
    for start in range(0, len(id_list), FETCH_BATCH_SIZE):
        batch_ids = id_list[start:start + FETCH_BATCH_SIZE]
        ids = ",".join(batch_ids)
        params = {
            "db": "pubmed",
            "id": ids,
            "retmode": "json"
        }

        query_string = urllib.parse.urlencode(params)
        url = f"{ESUMMARY_URL}?{query_string}"

        try:
            with urllib.request.urlopen(url) as response:
                result_json = json.loads(response.read().decode("utf-8"))
                result_body = result_json.get("result", {})

                for pmid in batch_ids:
                    metadata = result_body.get(str(pmid)) or result_body.get(pmid)
                    if not metadata:
                        continue

                    authors = metadata.get("authors", [])
                    author_names = [author.get("name", "") for author in authors if author.get("name")]
                    author_preview = ", ".join(author_names[:3]) if author_names else "Unknown Author"
                    pubdate = metadata.get("pubdate", "Unknown")
                    journal = metadata.get("source", "Unknown Journal")
                    title = metadata.get("title", "No title available")
                    year_match = re.search(r"\d{4}", str(pubdate))

                    paper = {
                        "pmid": str(pmid),
                        "title": title,
                        "year": year_match.group(0) if year_match else "Unknown",
                        # esummary 不返回摘要，这里保留一个高信息量的元数据摘录，
                        # 供快速写作阶段参考。
                        "abstract": f"Title: {title}. Journal: {journal}. PubDate: {pubdate}. Authors: {author_preview}.",
                    }
                    papers.append(paper)
        except Exception as e:
            print(f"Error fetching details: {e}", file=sys.stderr)

    return papers

def save_to_json(papers, section_name, query, filename="references.json"):
    """
    Appends papers to the JSON file with the section tag and search query.
    """
    # 1. Add section tag and query
    for paper in papers:
        paper["section"] = section_name
        paper["search_query"] = query
        
    # 2. Load existing
    existing_data = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {filename} was corrupted or empty. Overwriting.", file=sys.stderr)
            existing_data = []
            
    # 3. Append (avoiding absolute duplicates if feasible, but simple append is safer for now)
    # We will just append. The read script can filter. 
    # Actually, let's avoid adding the EXACT same PMID for the SAME section.
    
    existing_ids = set((p.get("pmid"), p.get("section")) for p in existing_data)
    
    added_count = 0
    for paper in papers:
        key = (paper.get("pmid"), section_name)
        if key not in existing_ids:
            existing_data.append(paper)
            added_count += 1
            
    # 4. Save
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
    return added_count

def main():
    parser = argparse.ArgumentParser(description="Search PubMed and save to references.json.")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("--section", required=True, help="Section name (e.g., 'Introduction')")
    parser.add_argument("--max", type=int, default=DEFAULT_MAX_RESULTS, help="Max results to return")
    parser.add_argument("--file", default="references.json", help="Output JSON file")
    parser.add_argument("--post-write", action="store_true", help="Flag to indicate this is a supplementary search after writing.")
    
    args = parser.parse_args()

    # Validate section name format
    # Allowed: 'introduction' OR 'section_N' (where N is a number)
    if not re.match(ALLOWED_SECTION_PATTERN, args.section):
        print(f"Error: Invalid section name '{args.section}'.", file=sys.stderr)
        print("Allowed formats: 'introduction', 'section_N', 'global_pool', or 'master_library'.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Searching for: {args.query}...", file=sys.stderr)
    id_list = search_pubmed(args.query, args.max)
    
    if not id_list:
        print("No results found.", file=sys.stderr)
        return

    papers = fetch_details(id_list)
    
    # Save to file
    added = save_to_json(papers, args.section, args.query, args.file)
    
    print(f"Successfully fetched {len(papers)} papers.")
    print(f"Added {added} new unique papers to {args.file} under section '{args.section}'.")
    
    # Optionally print a brief summary for the agent to see immediately
    for p in papers[:3]:
        print(f"- {p.get('title')} ({p.get('year')}) [PMID: {p.get('pmid')}]")

    print("\n" + "="*40)
    print("【状态机 (State Machine)】")
    if getattr(args, 'post_write', False):
        print("当前状态: 阶段三 (分章撰写) - 写作后补充检索完成。")
        print(f"下一步建议: ")
        print(f"- 新检索到的文献已追加至 {args.file} 的 `{args.section}` 标签下。")
        print("- 请运行 `read_references.py` 获取最新文献内容，并补充到刚写完的章节 `.md` 文件中以增加参考文献数。")
    else:
        print(f"当前状态: 阶段二 (Data Retrieval) - 检索完成。已为章节 `{args.section}` 检索文献。")
        print("下一步建议: ")
        print("- 若需要继续为其他章节检索，请继续运行此脚本。")
        print("- 若所有章节检索完毕，请运行 `count_references.py` 检查文献总数。")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
