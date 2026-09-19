"""TRIPOD-AI / TRIPOD-ML 预测模型评价清单（v1.2.0）。

TRIPOD-AI 是 TRIPOD 在人工智能/机器学习预测模型领域的扩展声明（Liu et al. 2021, BMJ / Nature Medicine），
本文件实现其 12+ 条与 ML/DL 模型密切相关的新增条目。

要点：
- 主要针对 ROC、Scatter（calibration plot）两类图，因为它们最常用于预测模型评估
- 当 raw["model_type"] 表明是 ML/DL 模型时追加到评价清单
- 自动评估基于 raw 字段：data_source、external_validation_temporal、external_validation_geographic、
  explainability_method、fairness_assessed、code_availability、data_availability 等

条目分类：
  TRIPOD-AI-1  模型类型是否明确（逻辑回归 / 随机森林 / XGBoost / NN / Transformer…）
  TRIPOD-AI-2  训练数据来源与时间窗
  TRIPOD-AI-3  样本量与 EPP（events per predictor）是否报告
  TRIPOD-AI-4  训练/测试划分策略（随机 / 时间 / 地理）
  TRIPOD-AI-5  内部验证方法（bootstrap / k-fold / split-sample）
  TRIPOD-AI-6  时间外部验证
  TRIPOD-AI-7  地理外部验证（独立机构 / 多中心）
  TRIPOD-AI-8  calibration（slope + intercept + brier score）
  TRIPOD-AI-9  可解释性（SHAP / LIME / feature importance / attention）
  TRIPOD-AI-10 亚组公平性（age / sex / race / institution）
  TRIPOD-AI-11 决策曲线 / 临床效用
  TRIPOD-AI-12 代码与数据可获得性（reproducibility）
  TRIPOD-AI-13 模型版本（card / 参数冻结）
  TRIPOD-AI-14 偏差评估（数据来源 / 选择 / label bias）
"""
from __future__ import annotations

from typing import Any

from parsers.base import StatisticalSummary
from appraisal import ChecklistItem


# ML / DL 模型关键词（不区分大小写）— v1.4.0 扩展到 60+
_ML_MODEL_KEYWORDS = {
    # 经典 ML
    "logistic", "logistic_regression", "regression",
    "random_forest", "rf", "xgboost", "xgb", "lightgbm", "lgbm",
    "svm", "support_vector", "knn", "naive_bayes", "decision_tree",
    "gradient_boosting", "gbm", "catboost", "adaboost", "extra_trees",
    # 深度学习（经典）
    "neural_network", "neural", "nn", "dnn", "deep_learning", "deep",
    "cnn", "rnn", "lstm", "gru", "attention", "transformer", "bert",
    "resnet", "vgg", "inception", "u_net", "unet", "vit", "swin",
    # 新兴架构 / 范式 (v1.4.0)
    "tabnet", "tabpfn", "node", "tab_transformer",
    "causal_forest", "causal_tree", "causal_inference", "uplift",
    "federated", "federated_learning", "split_learning",
    "diffusion", "gan", "autoencoder", "vae",
    "reinforcement", "rl", "policy_network", "dqn", "ppo",
    # 大模型 / LLM (v1.4.0)
    "gpt", "gpt-3", "gpt-3.5", "gpt-4", "gpt-4o", "llm", "claude", "llama",
    "qwen", "mistral", "gemini", "deepseek", "chinese_llama", "chatglm",
    "foundation_model", "pretrained", "fine_tuning", "finetuned", "adapter",
    "rag", "retrieval_augmented", "few_shot", "zero_shot",
    # 命名实体
    "ml", "machine_learning", "dl", "ai", "artificial_intelligence",
    "clinical_nlp", "nlp",
}


# 检测 raw 是否声明了 ML 训练超参（辅助触发 v1.4.0）
_ML_HYPERPARAM_FIELDS = {
    "learning_rate", "epochs", "batch_size", "loss_fn", "loss_function",
    "optimizer", "weight_decay", "l1", "l2", "dropout", "warmup_steps",
    "early_stopping", "gradient_accumulation",
}


def _is_ml_model(raw: dict) -> bool:
    """检查 raw 是否声明了 ML/DL 模型（v1.4.0 三路触发）。"""
    # 1) model_type / model_name 命中关键词
    mt = (raw.get("model_type") or raw.get("model_name") or "").lower()
    if mt and any(kw in mt for kw in _ML_MODEL_KEYWORDS):
        return True
    # 2) methodology / algorithm 字段
    for f in ("methodology", "algorithm", "predictor_type"):
        v = (raw.get(f) or "").lower()
        if v and any(kw in v for kw in _ML_MODEL_KEYWORDS):
            return True
    # 3) 出现任何超参字段
    if any(f in raw for f in _ML_HYPERPARAM_FIELDS):
        return True
    return False


# TRIPOD-AI 条目定义（id, question, framework, raw_field, expected_type）
_TRIPOD_AI_ITEMS: list[tuple[str, str, str, str, type]] = [
    ("TRIPOD-AI-1", "是否明确声明所用模型类型（如 XGBoost / ResNet / Transformer）？",
     "TRIPOD-AI", "model_type", str),
    ("TRIPOD-AI-2", "是否报告训练数据来源、时间窗与样本量？",
     "TRIPOD-AI", "data_source", str),
    ("TRIPOD-AI-3", "事件数 / 预测因子数（EPP）是否报告？通常要求 ≥ 10。",
     "TRIPOD-AI", "events_per_predictor", (int, float)),
    ("TRIPOD-AI-4", "训练 / 测试划分策略（随机 / 时间分层 / 地理划分）是否说明？",
     "TRIPOD-AI", "split_strategy", str),
    ("TRIPOD-AI-5", "内部验证方法（bootstrap / k-fold / split-sample）是否实施？",
     "TRIPOD-AI", "internal_validation", str),
    ("TRIPOD-AI-6", "是否有时间外部验证（同一机构、不同时间段或前瞻队列）？",
     "TRIPOD-AI", "external_validation_temporal", bool),
    ("TRIPOD-AI-7", "是否有地理外部验证（独立机构 / 多中心）？",
     "TRIPOD-AI", "external_validation_geographic", bool),
    ("TRIPOD-AI-8", "calibration（slope / intercept / Brier score）是否报告？",
     "TRIPOD-AI", "calibration_slope", (int, float)),
    ("TRIPOD-AI-9", "可解释性方法（SHAP / LIME / feature importance / attention）是否使用？",
     "TRIPOD-AI", "explainability_method", str),
    ("TRIPOD-AI-10", "亚组公平性（age / sex / race / 机构）是否评估？",
     "TRIPOD-AI", "fairness_assessed", bool),
    ("TRIPOD-AI-11", "决策曲线分析（DCA） / 临床净收益是否给出？",
     "TRIPOD-AI", "decision_curve", bool),
    ("TRIPOD-AI-12", "代码与训练数据可获得性（GitHub / 公开数据集）是否说明？",
     "TRIPOD-AI", "code_availability", str),
    ("TRIPOD-AI-13", "模型版本号 / 随机种子 / 超参数是否锁定？",
     "TRIPOD-AI", "model_version_pinned", bool),
    ("TRIPOD-AI-14", "潜在偏倚（数据来源偏差 / 标签偏差 / 选择偏差）是否讨论？",
     "TRIPOD-AI", "bias_assessed", bool),
]


def build_tripod_ai_items(raw: dict | None) -> list[ChecklistItem]:
    """根据 raw 是否声明 ML 模型，返回对应 ChecklistItem 列表（用于追加到评价结果）。

    v1.4.0：若 _is_ml_model 通过但 14 项均未匹配（如只声明了 learning_rate 等超参），
    追加一个 sentinel "TRIPOD-AI-0" 让 reviewer 知道进入 ML 场景。
    """
    raw = raw or {}
    items: list[ChecklistItem] = []
    matched_any = False
    for item_id, question, framework, raw_field, expected_type in _TRIPOD_AI_ITEMS:
        item = ChecklistItem(id=item_id, question=question, framework=framework)
        value = raw.get(raw_field)
        if value is None:
            # 未报告 → 留给人工判定
            continue
        matched_any = True
        # 自动评估（按字段类型判定）
        if expected_type is bool:
            item.passed = bool(value)
            item.note = f"{raw_field}={value}"
        elif isinstance(expected_type, tuple):
            # 多类型 (int, float)：用 isinstance 判定
            if isinstance(value, expected_type):
                item.passed = True
                item.note = f"{raw_field}={value}"
            else:
                item.note = f"{raw_field}={value} (type mismatch)"
        elif expected_type is str:
            if isinstance(value, str) and value.strip():
                item.passed = True
                item.note = f"{raw_field}={value[:30]}"
        elif isinstance(value, expected_type):
            item.passed = True
            item.note = f"{raw_field}={value}"
        items.append(item)

    # 仅有模型类型/超参触发、14 项未匹配 → 留 sentinel
    if not matched_any and _is_ml_model(raw):
        items.append(ChecklistItem(
            id="TRIPOD-AI-0",
            question="已识别 ML/DL 模型：其余 14 项评价所需的报告字段是否齐备？",
            passed=None,
            note="已通过超参或 methodology 字段识别 ML 模型；data_source/EPP/validation/calibration 等标准字段未见——建议向作者索要完整 TRIPOD-AI 信息",
            framework="TRIPOD-AI",
        ))
    return items


def evaluate_tripod_ai(summary: StatisticalSummary) -> tuple[bool, list[ChecklistItem]]:
    """入口：判断该 summary 是否触发 TRIPOD-AI 评价，返回 (是否触发, 评价项)。"""
    raw = summary.raw or {}
    triggered = _is_ml_model(raw)
    items = build_tripod_ai_items(raw) if triggered else []
    return triggered, items
