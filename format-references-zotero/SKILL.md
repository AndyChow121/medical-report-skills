---
name: format-references-zotero
description: >
  Zotero 版文献排版工作流。将 Markdown 手稿中的 [PMID: xxxx] 标记转换为 Word (.docx)，直接写入原生 Zotero 域代码（ADDIN ZOTERO_ITEM / ADDIN ZOTERO_BIBL），用户在 Word 中点一次「Refresh」即可完成排版。
  内置 search_styles.py 脚本可搜索/下载任意 CSL 引用样式（Science、Nature、Vancouver、APA 等），process_references.py 支持指定任意样式输出。
  仅适用于 Zotero 用户；EndNote 用户请使用 format-references-endnote skill。
  触发词：「处理文献」「排版引用」「格式化参考文献」「PMID 转 Word」「导入 Zotero」「处理手稿」「Zotero 排版」「format references zotero」「cite to word」「把文献排好」「转成 Word」「文献导入」「参考文献排版」「下载csl」「装样式」「安装引用格式」「search style」「science格式」「nature格式」「换样式」等涉及参考文献排版或 CSL 样式下载的场景。
---

# Medical Literature Reference Formatter — Zotero 版

将 `[PMID: xxxx]` 标记直接转换为 Word 原生 Zotero 域代码，保持完整的可编辑性：用户可在 Zotero 中随时切换引用样式，Word 里一键 Refresh 全文更新。

## Workflow

### Step 0 — 检查环境（首次或报错时）

```bash
python "<skill_dir>/scripts/check_env.py"
```

检查：Python、python-docx、Pandoc、PubMed API、Zotero 安装及运行状态。

若提示 `.ris 未关联到 Zotero`，询问用户是否修复，同意后运行：

```bash
python "<skill_dir>/scripts/check_env.py" --fix-ris
```

### Step 1 — 确认目标文件

用户未给出完整路径时询问。桌面路径：`C:\Users\<username>\Desktop\<filename>.md`

### Step 2 — 确认引用样式

默认使用 `nature`。如果用户指定了其他样式（如 Vancouver、Elsevier、APA），先确认该样式已安装：

```bash
python "<skill_dir>/scripts/search_styles.py" <keyword>          # 搜索可用样式
python "<skill_dir>/scripts/search_styles.py" --install <style-id>  # 下载并安装
```

样式会自动安装到 Zotero 本地样式目录（通过读取 `prefs.js` 定位，跨平台可用）。

### Step 3 — 运行处理脚本

```bash
python "<skill_dir>/scripts/process_references.py" "<absolute_path>" [--style <style-id>]
```

默认样式为 `nature`，可指定任意已安装的样式 ID：

```bash
python "<skill_dir>/scripts/process_references.py" "paper.md" --style elsevier-harvard
python "<skill_dir>/scripts/process_references.py" "paper.md" --style vancouver
```

脚本完成：PMID 提取 → PubMed 元数据 → 生成带 Zotero 域的 .docx（含 ZOTERO_PREF）→ 生成 .ris → 自动打开。

### Step 3.5 — 换样式 / 强制刷新缓存

```bash
python "<skill_dir>/scripts/process_references.py" "paper.md" --style vancouver
python "<skill_dir>/scripts/process_references.py" "paper.md" --force-refresh   # 清除缓存，重新拉取 PubMed
```

缓存文件 `<stem>_pubmed_cache.json` 自动生成在 `.md` 同目录下，避免每次重复拉取 PubMed。添加新 PMID 后只需正常跑一次，已有文献走缓存，仅拉取新增的。

### Step 4 — 完整性检查

脚本拉完 PubMed 后会自动检查：如果某个 PMID 获取失败，会列出具体编号并提示用 `--force-refresh` 重试。

### Step 5 — 处理常见问题

**Pandoc 未安装**：https://pandoc.org/installing.html

**python-docx 未安装**：`pip install python-docx`

**PubMed 无法访问**：网络问题，稍后重试。

**Zotero 未运行**：打开 Zotero 桌面版后，Word 里 Refresh 才能格式化引用。

**样式未安装**：运行 `search_styles.py --install <style-id>` 自动下载安装。

### Step 6 — 告知用户

> 文档已生成，.ris 已导入 Zotero 库。请在 Word 中点击 Zotero 选项卡的「Refresh」完成排版。之后如需换样式，运行 change_style.py 指定新样式，再 Refresh 一次即可全文更新。

## 输出文件

| 文件 | 说明 |
|------|------|
| `<stem>-zotero.docx` | 含 Zotero 域代码的 Word 文档 |
| `<stem>.ris` | 文献数据，导入 Zotero 库（与 EndNote 版共用） |
| `<stem>_pubmed_cache.json` | PubMed 元数据缓存，避免重复拉取 |

## 引用样式管理（search_styles.py）

本 skill 自带 `search_styles.py` 脚本，用于搜索和安装 CSL 引用样式，**无需离开命令行或手动下载 .csl 文件**。

### 搜索可用样式

```bash
python "<skill_dir>/scripts/search_styles.py" <关键词>
```

关键词可以是期刊名或样式名（中英文均可），例如：

```bash
python "<skill_dir>/scripts/search_styles.py" science       # 搜索 Science 相关样式
python "<skill_dir>/scripts/search_styles.py" nature        # 搜索 Nature 相关样式
python "<skill_dir>/scripts/search_styles.py" vancouver     # 搜索 Vancouver 编号样式
python "<skill_dir>/scripts/search_styles.py" elsevier      # 搜索 Elsevier 旗下期刊样式
python "<skill_dir>/scripts/search_styles.py" chinese       # 搜索中文期刊样式
```

### 安装样式到 Zotero

从搜索结果中找到想要的 `样式 ID`，然后安装：

```bash
python "<skill_dir>/scripts/search_styles.py" --install <style-id>
```

示例：

```bash
python "<skill_dir>/scripts/search_styles.py" --install science         # Science 期刊
python "<skill_dir>/scripts/search_styles.py" --install vancouver-nlm   # Vancouver 编号
python "<skill_dir>/scripts/search_styles.py" --install nature          # Nature
python "<skill_dir>/scripts/search_styles.py" --install elsevier-harvard # Elsevier Harvard
```

样式会自动下载到 Zotero 的本地样式目录（`~Zotero/styles/`），重启 Zotero 后在 Word 中即可选用。

### 用安装的样式生成 Word 文档

安装样式后，在 Step 3 的 `process_references.py` 中通过 `--style` 指定已安装的样式 ID：

```bash
python "<skill_dir>/scripts/process_references.py" "paper.md" --style science
python "<skill_dir>/scripts/process_references.py" "paper.md" --style vancouver-nlm
```

### 支持的样式来源

脚本从 Zotero 官方样式仓库（`https://www.zotero.org/styles`）搜索，**覆盖 9000+ 种期刊和机构的 CSL 样式**，包括但不限于：

- Science / Nature / Cell / PNAS / JAMA / NEJM / Lancet / BMJ
- APA / MLA / Chicago / Vancouver / Harvard
- 各大学学位论文格式
- 中文期刊（科学通报、中国科学等）
- 各出版社定制格式（Elsevier、Springer、Taylor & Francis 等）

## 域代码原理

脚本将每处 `[PMID: xxxx]` 替换为 `ADDIN ZOTERO_ITEM CSL_CITATION` 域，内嵌完整 CSL JSON 元数据，末尾插入 `ADDIN ZOTERO_BIBL` 域。Zotero 的 Word 插件识别这两种域，Refresh 时按当前样式格式化全部引用和参考文献表。

流程：
1. Pandoc 将 Markdown 编译为中间 .docx（含 `ZRCITE{pmid}` 标记）
2. python-docx 打开 .docx，将标记替换为 Word 域代码（w:fldChar / w:instrText）
3. 注入 ZOTERO_PREF 域，确保 Refresh 后样式持久化

## 环境要求

- **Python 3.7+**
- **python-docx** — `pip install python-docx`
- **Pandoc** — https://pandoc.org/installing.html
- **Zotero 桌面版** + Word 插件（Zotero 需在 Refresh 时运行）
- **网络** — 访问 PubMed API
