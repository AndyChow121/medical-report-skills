---
name: format-references-endnote
description: >
  EndNote 版文献排版工作流 — 将 Markdown 手稿中的 [PMID: xxxx] 标记转换为 Word (.docx)，使用 EndNote CWYW 识别的 {Author, Year, Title} 占位符，同时生成 .ris 文件自动导入本地 EndNote 库，用户在 Word 中点一次「Update Citations」即可完成排版。
  仅适用于使用 EndNote 的场景；Zotero 用户请使用 format-references-zotero skill。
  触发词：「处理文献」「排版引用」「格式化参考文献」「PMID 转 Word」「导入 EndNote」「处理手稿」「EndNote 排版」「format references endnote」「cite to word」「把文献排好」「转成 Word」「文献导入」「参考文献排版」，或任何提到 [PMID:] 标记且上下文涉及 EndNote 的场景。
---

# Medical Literature Reference Formatter

This skill automates the step of turning rough `[PMID: xxxx]` citation markers into professionally formatted Word documents that work with EndNote's one-click bibliography generation. No COM automation or macros — purely file-based, stable on any machine with Python + Pandoc.

## When you're invoked

The user has a Markdown manuscript with inline `[PMID: xxxx]` markers and wants a `.docx` with citation placeholders that EndNote can resolve into a formatted bibliography.

## Workflow

### Step 0 — Check environment (first time or on error)

If this is the first run, or the user reports any unexpected error, run the bundled check script first:

```bash
python "<skill_dir>/scripts/check_env.py"
```

It verifies: Python 3.7+, Pandoc, PubMed API connectivity, EndNote installation, and `.ris` file association.

If the output shows `.ris 未关联到 EndNote`, ask the user: "是否将 .ris 文件的默认打开方式改为 EndNote？改了之后生成文件会自动触发导入。" If they agree, run:

```bash
python "<skill_dir>/scripts/check_env.py" --fix-ris
```

### Step 1 — Confirm the target file

If the user didn't specify a full path, ask. If they give a vague location like "on my Desktop", resolve it:
- Windows: `C:\Users\<username>\Desktop\<filename>.md`
- macOS: `/Users/<username>/Desktop/<filename>.md`

### Step 2 — Run the bundled processing script

The Python script is at `scripts/process_references.py` inside this skill's directory. Find the skill directory from the path this SKILL.md was loaded from, then run:

```bash
python "<skill_dir>/scripts/process_references.py" "<absolute_path_to_file.md>"
```

The script handles the entire pipeline: PMID extraction → PubMed API fetch → placeholder substitution → Pandoc compile → RIS generation → auto-open both files.

**缓存机制**：首次运行后生成 `<stem>_pubmed_cache.json`，后续运行自动复用缓存，避免重复拉取 PubMed。添加新 PMID 时仅拉取新增的。

**强制刷新**：`python process_references.py "<file>" --force-refresh` 清除缓存重新拉取。

### Step 3 — Handle failures gracefully

**Pandoc not found**: Tell the user to install it from https://pandoc.org/installing.html, then re-run.

**PubMed API unreachable**: The script fills failed PMIDs with `{PMIDxxxxx, n.d., [fetch failed]}` so the document is still generated. Offer to retry when network is available.

**File path issues**: Confirm the path exists and has the `.md` extension, then re-run.

**EndNote not opening automatically**: The `.ris` file association may not be configured. Tell the user to open EndNote manually and drag `references_temp.ris` into the library window.

### Step 4 — Deliver the result

After the script exits successfully, say:

> 文献已自动导入 EndNote，文档已打开。请在 Word 中切换到 EndNote 选项卡，点击「Update Citations and Bibliography」即可完成排版。

Also note the output files are saved **in the same directory as the original .md file**.

## Output files

| File | Purpose |
|------|---------|
| `<stem>-endnote.docx` | Word doc with `{Author, Year, Title}` unformatted citation placeholders |
| `<stem>.ris` | All references in RIS format — opening this imports them into EndNote |
| `<stem>_pubmed_cache.json` | PubMed metadata cache — avoids repeated network fetches |

## Why this approach works

EndNote's CWYW (Cite While You Write) engine recognizes `{Author, Year, Title}` as an "unformatted citation". When the user clicks **Update Citations**, EndNote scans the document, matches placeholders against the library, and formats them according to the selected style. This is entirely text-based — no macros, no COM, no risk of security dialogs or permission prompts.

## Title normalization

The script automatically normalizes titles to ensure EndNote CWYW can match citation placeholders against the RIS-imported library:

| Transformation | Example |
|---|---|
| Greek letters → Latin | `α-synuclein` → `alpha-synuclein` |
| Smart quotes → ASCII | `'` `"` → `'` `"` |
| Em/en dashes → hyphens | `—` → `--`, `–` → `-` |
| Brackets stripped | `[Ca²⁺]` → `Ca²⁺` |
| Commas stripped | (field delimiter in `{Author, Year, Title}`) |
| Trailing period stripped | (some libraries omit it) |

Both the docx placeholder and the RIS file (TI field) use the **identical normalized title**.

## Troubleshooting

**"Update Citations" 很多找不到**: Caused by title mismatch between docx and RIS. Re-run with `--force-refresh` to regenerate with normalized titles. Verify all records imported into EndNote.

**EndNote crashes during Update**: Split the work — select half the document, update, then the other half.

## Requirements

- **Python 3.7+** with standard library only (no pip installs needed)
- **Pandoc** for `.md → .docx` conversion
- **Internet access** for NCBI PubMed API calls
- **EndNote** installed, with `.ris` file association configured
