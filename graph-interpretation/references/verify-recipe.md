# graph-interpretation CI 自检配方（v1.6.0）

`graph-interp verify` 一行命令即可跑通全部 bundled samples（10 个：8 类基础 + ML + 中文期刊）。
适合作为 GitHub Actions / 本地 CI 的最后一道闸。

## 1. 最简接入（5 行）

```yaml
# .github/workflows/ci.yml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"

- name: Install skill
  run: pip install ~/.workbuddy/skills/graph-interpretation

- name: Verify end-to-end
  run: graph-interp verify
```

非零退出码即有 sample 失败；详细列表由命令本身打印。

## 2. 关键标志

| 标志 | 默认 | 说明 |
|------|------|------|
| `--no-ml` | off | 跳过 roc_ml 样本（默认包含） |
| `--no-zh` | off | 跳过 csco_km 样本（默认包含） |
| `--work-dir DIR` | `.verify_tmp` | docx 产物目录 |
| `--cleanup` | off | 完成后删除产物目录（CI 推荐开启） |

## 3. 退出码语义

- `0`  → 全部样本通过
- `N (1-255)` → 失败样本数（最多 255）

CI 中可用 `if [ $? -ne 0 ]` 直接判定失败。

## 4. 性能基线（v1.5.0，Windows / Python 3.13）

| 步骤 | 单 sample 平均 |
|------|---------------|
| interpret + caption + audiences + appraise | ~50ms |
| render-svg | ~10ms |
| to-legend(docx) | ~120ms |
| **合计** | ~180ms |
| **10 sample 整轮** | ~1.8s |

可在 CI 内做 baseline 比较；如果超过基线 2x，则有性能退化。

## 5. 失败排查

若 verify 失败，保留 `--work-dir` 产物：

```bash
graph-interp verify --work-dir artifacts
# 失败后：
ls artifacts/verify_*.docx
# 看哪个 sample 产物缺失 / 大小异常
```

逐项排查：

```bash
graph-interp interpret --type roc --data scripts/sample_roc.json
graph-interp caption   --type roc --data scripts/sample_roc.json --style cma --language zh
graph-interp audiences --type roc --data scripts/sample_roc.json --locale zh_CN
graph-interp appraise  --type roc --data scripts/sample_roc.json
graph-interp render-svg --type roc --data scripts/sample_roc.json --out /tmp/roc.svg
graph-interp to-legend --type roc --data scripts/sample_roc.json --mode docx \
    --figure-number 1 --out /tmp/roc.docx
```

## 6. 与 figure-legend-gen / medical-literature-report 的协同 CI

graph-interpretation 的 verify 是 medical-literature-report 的"图解读节点"的
最小依赖校验。建议两 Skill 都装：

```bash
pip install ~/.workbuddy/skills/graph-interpretation
pip install ~/.workbuddy/skills/figure-legend-gen
graph-interp verify --cleanup
```

如果后续要更严格的端到端（含 figure-legend-gen 的 LegendGenerator 真实调用），
可另开一个 `verify_bridge` 子任务（v1.5.1+ 候选）。

## 7. v1.4.0 → v1.5.0 verify 差异

| 版本 | 样本数 | 端到端项 | 备注 |
|------|--------|----------|------|
| v1.4.0 | 3 (硬编码) | interpret+caption+ocr+3 类 svg | `check` 子命令 |
| v1.5.0 | 10 (bundled) | 6 步全链路 | `verify` 子命令 |
| **v1.6.0** | 10 (bundled) | 6 步全链路 + 质量阈值 | `verify` + `pytest` + CI |

CI 推荐从 v1.4.0 的 `graph-interp check` 切换到 v1.5.0+ 的 `graph-interp verify`。

---

# v1.6.0 新增：质量阈值、单元测试与 GitHub Actions

## 8. verify 质量阈值（v1.6.0）

v1.5.0 的 verify 只回答「链路跑没跑通」。v1.6.0 起可以回答
「质量达不达标」——这对 bundled sample 的回归尤其有用。

### 两个阈值

| 参数 | 判定 | 典型取值 |
|------|------|----------|
| `--fail-on-low-score F` | `overall_score < F` 判失败（F 取 0-1） | `0.6` ~ `0.8` |
| `--fail-on-missing N` | `n_unchecked > N` 判失败 | `3` ~ `5` |

两者默认关闭，保持「跑通即通过」的向后兼容语义。

### 退出码语义

退出码 = 失败样本数（0 = 全部达标），CI 可直接 `if [ $? -ne 0 ]` 判定。

```bash
graph-interp verify --cleanup                          # 0（仅验链路）
graph-interp verify --cleanup --fail-on-low-score 0.7  # 4（bar/forest/scatter/heatmap 不达标）
graph-interp verify --cleanup --fail-on-missing 2      # 8（未评估条目过多）
```

### 按得分升序的汇总表

无论是否启用阈值，verify 都会输出一张汇总表，低分样本排最前：

```
=== 汇总（按得分升序）===
  样本             类型                 得分    条目    通过    未评   状态
  --------------------------------------------------------------
  bar            bar_chart         50%     6     1     4   OK
  forest         forest_plot       60%     9     3     4   OK
  heatmap        heatmap           67%     6     2     3   OK
  roc_ml         roc_curve        100%    29    24     5   OK
```

这张表本身就是 bundled sample 的「健康体检报告」：一眼看出哪些样本
数据单薄（大量未评估条目）、哪些数据充分。

### 建议的 CI 阶梯

```bash
# 第一道：链路必须全通（硬门禁）
graph-interp verify --cleanup

# 第二道：质量门槛（软门禁，可先只告警）
graph-interp verify --cleanup --fail-on-low-score 0.5 || \
  echo "::warning::部分 bundled sample 得分偏低"
```

## 9. pytest 单元测试（v1.6.0）

`tests/` 目录下 4 个测试文件，共 70 个用例，全量跑约 0.5 秒。

| 文件 | 覆盖 |
|------|------|
| `tests/test_parsers.py` | 8 类解析器：返回结构、JSON 可序列化、解析确定性 |
| `tests/test_schema.py` | JSON Schema：样本通过、越界值拒绝、缺字段拒绝 |
| `tests/test_diff.py` | diff 模块：自比无差异、方向敏感性、三档渲染格式 |
| `tests/test_end_to_end.py` | 全链路：caption / audiences / appraise / render-svg + TRIPOD-AI 触发 |

### 运行

```bash
pip install . pytest python-docx
pytest tests/ -q
```

### conftest.py 的作用

模块彼此以顶层方式 import（`from parsers import PARSERS`），
因此 `tests/conftest.py` 把 `scripts/` 插到 `sys.path` 最前：

```python
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
```

这让测试既能在本仓库跑，也能在 pip 安装态下指向 site-packages。

## 10. GitHub Actions 工作流（v1.6.0）

`.github/workflows/ci.yml` 开箱即用：

```yaml
strategy:
  matrix:
    os: [ubuntu-latest]
    python-version: ["3.10", "3.11", "3.12", "3.13"]
    include:
      - os: windows-latest      # 额外覆盖 Windows，捕捉路径/编码回归
        python-version: "3.13"
```

### 六个阶段

| 阶段 | 命令 | 门禁意义 |
|------|------|----------|
| 1. 单元测试 | `pytest tests/ -q` | 解析 / schema / diff 逻辑不回归 |
| 2. CLI 冒烟 | `graph-interp check` + `demo` | 入口点与 bundled sample 加载正常 |
| 3. 端到端自检 | `graph-interp verify --cleanup` | 10 个样本 6 步全链路 |
| 4. Schema 校验 | 循环 `validate --type $t` | 每个样本符合各自 schema |
| 5. diff 冒烟 | `graph-interp diff roc_partial_ml roc_ml` | v1.6.0 新子命令可用 |
| 6. wheel 校验 | 解压断言 sample 数 ≥ 20 | 资源确实打进了 wheel |

第 6 步是 v1.5.0 遗留的「wheel 内容 sanity check」自动化：
sample 资源一旦漏打包，`demo` 和 `verify` 会全线失效，
所以在 CI 里用断言守住。