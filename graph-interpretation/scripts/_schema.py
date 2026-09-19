"""graph-interpretation v1.5.0 —— JSON Schema 定义 + 轻量校验器。

不引入第三方依赖（jsonschema 等），手写最小校验器覆盖必填字段 + 类型检查。
外部脚本可参考 SCHEMAS 输出格式自行用 jsonschema 库做严格校验。

典型用法：

    from _schema import validate_payload, SCHEMAS, list_supported
    if validate_payload({"chart_type": "roc_curve", "auc": 0.9}):
        print("OK")
    else:
        print(validate_payload(...))   # 返回 (ok, errors)

CLI:
    graph-interp validate --data X.json --type roc
"""
from __future__ import annotations

from typing import Any


# ---------- JSON Schema 定义（手写，Subset of JSON Schema Draft 7） ----------

SCHEMAS: dict[str, dict] = {
    "kaplan_meier": {
        "type": "object",
        "required": ["title"],
        "properties": {
            "title": {"type": "string"},
            "hazard_ratio": {"type": "number"},
            "hr_ci": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
            "p_value": {"type": "number"},
            "n_total": {"type": "integer", "minimum": 0},
            "arms": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "median_survival": {"type": "number"},
                    },
                },
            },
            "at_risk": {"type": "object"},
            "schoenfeld_p": {"type": "number"},
        },
    },
    "forest_plot": {
        "type": "object",
        "required": ["title", "studies"],
        "properties": {
            "title": {"type": "string"},
            "measure": {"type": "string", "enum": ["OR", "RR", "HR", "MD", "SMD"]},
            "model": {"type": "string", "enum": ["fixed", "random"]},
            "i_squared": {"type": "number", "minimum": 0, "maximum": 100},
            "heterogeneity_p": {"type": "number"},
            "overall_effect": {"type": "number"},
            "overall_ci": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
            "overall_p": {"type": "number"},
            "studies": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["name", "effect"],
                    "properties": {
                        "name": {"type": "string"},
                        "effect": {"type": "number"},
                        "ci": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
                        "weight": {"type": "number"},
                        "n": {"type": "integer", "minimum": 0},
                    },
                },
            },
        },
    },
    "roc_curve": {
        "type": "object",
        "required": ["title"],
        "properties": {
            "title": {"type": "string"},
            "auc": {"type": "number", "minimum": 0, "maximum": 1},
            "auc_ci": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
            "curves": {"type": "array"},
            "optimal_cutoff": {"type": "number", "minimum": 0, "maximum": 1},
            "sensitivity": {"type": "number", "minimum": 0, "maximum": 1},
            "specificity": {"type": "number", "minimum": 0, "maximum": 1},
            "delong_p": {"type": "number"},
            # ML/TRIPOD-AI 字段（可选）
            "model_type": {"type": "string"},
            "data_source": {"type": "string"},
            "events_per_predictor": {"type": "number", "minimum": 0},
            "split_strategy": {"type": "string"},
            "internal_validation": {"type": "string"},
            "external_validation_temporal": {"type": "boolean"},
            "external_validation_geographic": {"type": "boolean"},
            "calibration_slope": {"type": "number"},
            "explainability_method": {"type": "string"},
            "fairness_assessed": {"type": "boolean"},
            "decision_curve": {"type": "boolean"},
            "code_availability": {"type": "string"},
            "model_version_pinned": {"type": "boolean"},
            "bias_assessed": {"type": "boolean"},
            # 超参字段（v1.4.0）
            "learning_rate": {"type": "number"},
            "epochs": {"type": "integer", "minimum": 0},
            "batch_size": {"type": "integer", "minimum": 1},
            "loss_fn": {"type": "string"},
            "optimizer": {"type": "string"},
        },
    },
    "scatter_plot": {
        "type": "object",
        "required": ["title"],
        "properties": {
            "title": {"type": "string"},
            "x_label": {"type": "string"},
            "y_label": {"type": "string"},
            "r_value": {"type": "number", "minimum": -1, "maximum": 1},
            "p_value": {"type": "number"},
            "n": {"type": "integer", "minimum": 0},
            "points": {"type": "array"},
        },
    },
    "box_plot": {
        "type": "object",
        "required": ["title", "groups"],
        "properties": {
            "title": {"type": "string"},
            "groups": {
                "type": "array",
                "minItems": 2,
                "items": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        # 多选 1：q1/median/q3 五数概括 OR values 数组
                        "values": {"type": "array", "items": {"type": "number"}},
                        "q1": {"type": "number"},
                        "median": {"type": "number"},
                        "q3": {"type": "number"},
                        "whisker_low": {"type": "number"},
                        "whisker_high": {"type": "number"},
                        "outliers": {"type": "array", "items": {"type": "number"}},
                        "n": {"type": "integer", "minimum": 0},
                    },
                },
            },
            "test": {"type": "string"},
            "p_value": {"type": "number"},
        },
    },
    "bar_chart": {
        "type": "object",
        "required": ["title"],
        "properties": {
            "title": {"type": "string"},
            "categories": {"type": "array", "items": {"type": "string"}},
            "values": {"type": "array", "items": {"type": "number"}},
            "error": {"type": "array"},
            # 替代形式：series[].values
            "series": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "values": {"type": "array", "items": {"type": "number"}},
                        "errors": {"type": "array"},
                    },
                },
            },
            "ylabel": {"type": "string"},
        },
    },
    "heatmap": {
        "type": "object",
        "required": ["matrix"],
        "properties": {
            "title": {"type": "string"},
            "row_labels": {"type": "array", "items": {"type": "string"}},
            "col_labels": {"type": "array", "items": {"type": "string"}},
            "matrix": {
                "type": "array",
                "items": {"type": "array", "items": {"type": "number"}},
            },
            "scale": {"type": "string", "enum": ["raw", "z-score", "min-max", "log"]},
            "colormap": {"type": "string"},
            "clustering_rows": {"type": "string"},
            "clustering_cols": {"type": "string"},
        },
    },
    "volcano_plot": {
        "type": "object",
        "required": ["title", "points"],
        "properties": {
            "title": {"type": "string"},
            "points": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    # 至少一个 p 值字段（p_value 或 neg_log10_p），至少一个名字字段（name 或 gene）
                    "properties": {
                        "name": {"type": "string"},
                        "gene": {"type": "string"},
                        "log2fc": {"type": "number"},
                        "p_value": {"type": "number"},
                        "neg_log10_p": {"type": "number"},
                        "significant": {"type": "boolean"},
                    },
                },
            },
            "fdr_method": {"type": "string"},
            "n_significant": {"type": "integer", "minimum": 0},
        },
    },
}


# 内部数据模型 schema（to_dict 输出后供跨 Skill 校验）
SCHEMA_STATISTICAL_SUMMARY = {
    "type": "object",
    "required": ["chart_type"],
    "properties": {
        "chart_type": {"type": "string"},
        "title": {"type": "string"},
        "primary": {"type": ["object", "null"]},
        "secondary": {"type": "array"},
        "notes": {"type": "array", "items": {"type": "string"}},
        "raw": {"type": "object"},
    },
}


# ---------- 轻量校验器 ----------

_TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _check(schema: dict, value: Any, path: str, errors: list[str]) -> None:
    """递归校验。"""
    expected_type = schema.get("type")
    if expected_type:
        py_types = _TYPE_MAP.get(expected_type)
        if py_types and not isinstance(value, py_types):
            # 兼容：JSON Schema "integer" 不接受 bool；Python 中 bool 是 int 子类，需特判
            if expected_type == "integer" and isinstance(value, bool):
                errors.append(f"{path}: expected integer, got boolean")
                return
            if not isinstance(value, py_types):
                errors.append(f"{path}: expected {expected_type}, got {type(value).__name__}")
                return

    if expected_type == "object":
        # required
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}.{req}: required field missing")

        # properties
        for key, sub_schema in schema.get("properties", {}).items():
            if key in value:
                _check(sub_schema, value[key], f"{path}.{key}", errors)

    elif expected_type == "array":
        items_schema = schema.get("items")
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if min_items is not None and len(value) < min_items:
            errors.append(f"{path}: array length {len(value)} < minItems={min_items}")
        if max_items is not None and len(value) > max_items:
            errors.append(f"{path}: array length {len(value)} > maxItems={max_items}")
        if items_schema:
            for i, item in enumerate(value):
                _check(items_schema, item, f"{path}[{i}]", errors)

    # enum
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value '{value}' not in enum {schema['enum']}")

    # 数字范围
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} < minimum={schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} > maximum={schema['maximum']}")


def validate_payload(payload: dict, schema_name: str = None) -> tuple[bool, list[str]]:
    """校验一个 dict 是否符合指定 schema。

    参数:
        payload: 待校验 dict
        schema_name: schema 名（如 'roc_curve'），None 则用 payload['chart_type']

    返回:
        (ok: bool, errors: list[str])
    """
    schema_name = schema_name or payload.get("chart_type")
    if not schema_name:
        return False, ["缺少 chart_type，且未指定 schema_name"]
    schema = SCHEMAS.get(schema_name)
    if not schema:
        return False, [f"未知 schema: {schema_name}（可选：{list(SCHEMAS)}）"]
    errors: list[str] = []
    _check(schema, payload, "$", errors)
    return (len(errors) == 0), errors


def list_supported() -> list[str]:
    """返回支持的 schema 名称列表。"""
    return sorted(SCHEMAS.keys())


def schema_to_text(schema_name: str) -> str:
    """以可读形式返回 schema（JSON 风格）。"""
    import json
    if schema_name not in SCHEMAS:
        return f"未知 schema: {schema_name}"
    return json.dumps(SCHEMAS[schema_name], ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 自检：跑遍 8 类 bundled samples
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _samples import load_bundled_sample

    TYPE_MAP = {
        "km": "kaplan_meier", "forest": "forest_plot", "roc": "roc_curve",
        "roc_ml": "roc_curve", "box": "box_plot", "scatter": "scatter_plot",
        "bar": "bar_chart", "heatmap": "heatmap", "volcano": "volcano_plot",
        "csco_km": "kaplan_meier",
    }

    print(f"=== graph-interpretation v1.5.0 schema validate ===")
    print(f"支持的 schema: {list_supported()}")
    print()
    n_ok, n_fail = 0, 0
    for alias in ["km", "forest", "roc", "roc_ml", "box", "scatter", "bar", "heatmap", "volcano", "csco_km"]:
        schema_name = TYPE_MAP.get(alias)
        if schema_name is None:
            continue
        try:
            data = load_bundled_sample(alias)
            ok, errors = validate_payload(data, schema_name)
            if ok:
                print(f"  [OK] {alias:10s} ({schema_name:14s})")
                n_ok += 1
            else:
                print(f"  [FAIL] {alias} ({schema_name}): {errors}")
                n_fail += 1
        except Exception as e:
            print(f"  [ERR] {alias}: {e}")
            n_fail += 1
    print(f"\n通过 {n_ok}/{n_ok+n_fail}")
    sys.exit(0 if n_fail == 0 else 1)