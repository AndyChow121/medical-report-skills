"""OCR 反向提取：从 PNG/JPG 图像中读出图表关键数字。

策略：
1) 优先尝试 pytesseract（轻量，跨平台）；
2) 若不可用，回退到纯文本正则匹配（用户提供 OCR 文本）；
3) 输出一个 best-effort 的 dict，便于喂给 parsers/。

说明：
- 这是 best-effort 工具，不承诺对所有图像都能解析。
- 对医学统计图，建议优先用 PDF 矢量提取（pdftotext / pdfplumber），
  再用本工具做兜底。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# 通用统计量正则
_PATTERNS: dict[str, re.Pattern[str]] = {
    "hazard_ratio": re.compile(r"\bHR\s*[=:]\s*([0-9.]+)\s*(?:\((?:95%?\s*CI[: ]\s*)?([0-9.]+)\s*[-–~]\s*([0-9.]+)\))?", re.I),
    "odds_ratio":   re.compile(r"\bOR\s*[=:]\s*([0-9.]+)\s*(?:\((?:95%?\s*CI[: ]\s*)?([0-9.]+)\s*[-–~]\s*([0-9.]+)\))?", re.I),
    "risk_ratio":   re.compile(r"\bRR\s*[=:]\s*([0-9.]+)\s*(?:\((?:95%?\s*CI[: ]\s*)?([0-9.]+)\s*[-–~]\s*([0-9.]+)\))?", re.I),
    "auc":          re.compile(r"\bAUC\s*[=:]\s*([0-9.]+)(?:\s*[\(\[]([0-9.]+)\s*[-–~]\s*([0-9.]+)[\)\]])?", re.I),
    "p_value":      re.compile(r"\bp\s*[<=>]\s*0?\.\d+", re.I),
    "log_rank_p":   re.compile(r"log[-\s]?rank\s*p\s*[<=>]\s*0?\.\d+", re.I),
    "i_squared":    re.compile(r"\bI[²2]\s*=\s*([0-9.]+)\s*%", re.I),
    "n_total":      re.compile(r"\bN\s*=\s*(\d{2,6})", re.I),
}


def extract_from_text(text: str) -> dict[str, Any]:
    """从 OCR 文本/纯文本中抽取关键统计量。"""
    out: dict[str, Any] = {}
    for key, pat in _PATTERNS.items():
        m = pat.search(text)
        if not m:
            continue
        if key in {"hazard_ratio", "odds_ratio", "risk_ratio"}:
            out[key] = {
                "value": float(m.group(1)),
                "ci": (
                    [float(m.group(2)), float(m.group(3))]
                    if m.group(2) and m.group(3)
                    else None
                ),
            }
        elif key == "auc":
            out["auc"] = float(m.group(1))
            if m.group(2) and m.group(3):
                out["auc_ci"] = [float(m.group(2)), float(m.group(3))]
        elif key in {"p_value", "log_rank_p"}:
            raw = m.group(0).lower()
            num = re.search(r"([0-9.]+)", raw)
            if num:
                p = float(num.group(1))
                out["p_value" if key == "p_value" else "logrank_p"] = p
        elif key == "i_squared":
            out["i_squared"] = float(m.group(1))
        elif key == "n_total":
            out["n_total"] = int(m.group(1))
    # 推断图表类型
    text_lower = text.lower()
    if "kaplan" in text_lower or "survival" in text_lower or "log-rank" in text_lower:
        out["_inferred_chart_type"] = "kaplan_meier"
    elif "auc" in text_lower and ("sensitivity" in text_lower or "specificity" in text_lower):
        out["_inferred_chart_type"] = "roc_curve"
    elif "i²" in text_lower or "heterogeneity" in text_lower or "random-effect" in text_lower:
        out["_inferred_chart_type"] = "forest_plot"
    elif "log2fc" in text_lower or "volcano" in text_lower:
        out["_inferred_chart_type"] = "volcano_plot"
    return out


def extract_from_image(path: str | Path) -> dict[str, Any]:
    """从图像中抽取关键统计量（需 pytesseract）。

    若 pytesseract 不可用，抛 RuntimeError 让调用方决定是否回退到文本路径。
    """
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "pytesseract/Pillow 未安装。请先 `pip install pytesseract Pillow`，"
            "并确保系统已安装 Tesseract OCR。"
        ) from e

    img = Image.open(path)
    text = pytesseract.image_to_string(img)
    result = extract_from_text(text)
    result["_ocr_text"] = text
    result["_source_image"] = str(path)
    return result


def extract_auto(path: str | Path, fallback_text: str | None = None) -> dict[str, Any]:
    """自动根据文件类型选择路径：
    - PDF → extract_from_pdf
    - 图片 → extract_from_image（失败则回退文本）
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_from_pdf(path)
    try:
        return extract_from_image(path)
    except RuntimeError:
        if fallback_text is None:
            return {"_error": "OCR unavailable and no fallback_text provided"}
        return extract_from_text(fallback_text)


# ---------- PDF 矢量抽取 ----------

# 在 PDF 文字流中识别"图表注释"的关键词
_FIG_CAPTION_HINTS = (
    "figure", "fig.", "fig ", "supplementary", "panel a", "panel b",
    "kaplan", "survival", "hazard", "forrest", "roc ", "sensitivity", "specificity",
    "volcano", "heatmap", "manhattan",
)


def _looks_like_figure_caption(text: str) -> bool:
    """启发式判断一段文本是否可能是图表注释/图注。"""
    if not text:
        return False
    lower = text.lower()
    if "figure" in lower and any(c in lower for c in ".:-–—"):
        return True
    if any(hint in lower for hint in _FIG_CAPTION_HINTS):
        # 倾向于短文本（< 600 字符）且含数字
        if len(text) < 800 and any(ch.isdigit() for ch in text):
            return True
    return False


def _merge_words(words: list[dict[str, Any]], y_tolerance: float = 3.0) -> list[str]:
    """把 pdfplumber 的 words 列表按 y 坐标分行，再拼接成字符串。"""
    if not words:
        return []
    words = sorted(words, key=lambda w: (round(w["top"] / y_tolerance), w["x0"]))
    lines: list[list[str]] = []
    current_y: float | None = None
    current: list[str] = []
    for w in words:
        y = w["top"]
        if current_y is None or abs(y - current_y) > y_tolerance:
            if current:
                lines.append(current)
            current = [w["text"]]
            current_y = y
        else:
            current.append(w["text"])
    if current:
        lines.append(current)
    return [" ".join(line) for line in lines]


def extract_from_pdf(path: str | Path) -> dict[str, Any]:
    """从 PDF 矢量文本中抽取图表数字。

    流程：
    1) 用 pdfplumber 逐页提取文字 + 图表区域附近的文字
    2) 每页同时把图注/标题附近的文本送入 extract_from_text
    3) 拼成一个 dict 返回

    若 pdfplumber 未安装，抛 RuntimeError，调用方可回退到 OCR/文本。
    """
    try:
        import pdfplumber  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "pdfplumber 未安装。请 `pip install pdfplumber` 后再试，"
            "或用 --text 模式提供文字兜底。"
        ) from e

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF 文件不存在: {path}")

    fragments: list[dict[str, Any]] = []
    full_text_parts: list[str] = []
    page_count = 0

    with pdfplumber.open(str(path)) as pdf:
        page_count = len(pdf.pages)
        for page_idx, page in enumerate(pdf.pages, start=1):
            # 整页文本
            page_text = page.extract_text() or ""
            if page_text:
                full_text_parts.append(page_text)

            # 矢量元素 + 文本块（更精确）
            chars = page.chars
            if chars:
                # 按页内位置抓"图注区域"（含 Figure 字样的整行）
                line_text = _merge_words(page.extract_words() or [])
                for line in line_text:
                    if _looks_like_figure_caption(line):
                        # 把这一行 + 后续 8 行打成一个 figure block
                        idx = line_text.index(line)
                        block = "\n".join(line_text[idx: idx + 9])
                        extracted = extract_from_text(block)
                        fragments.append({
                            "page": page_idx,
                            "matched_line": line,
                            "extracted": extracted,
                        })
                        break  # 每页只取第一个

    full_text = "\n".join(full_text_parts)
    best = extract_from_text(full_text) if full_text else {}

    # 把 fragments 里更高质量的字段合并进来（覆盖空字段）
    for frag in fragments:
        for k, v in frag["extracted"].items():
            if v is None:
                continue
            if k not in best or not best.get(k):
                best[k] = v

    best["_source_pdf"] = str(path)
    best["_pdf_pages"] = page_count
    best["_pdf_fragments"] = fragments[:20]   # 限制最多 20 条避免爆掉
    best["_pdf_full_text_chars"] = len(full_text)
    return best
