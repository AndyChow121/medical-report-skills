# Contributing · 贡献指南

> 中文 | English

欢迎为本套件贡献改进。本套件是 WorkBuddy 的 Skills 集合，每个 skill 自成一个目录。

## 约定 / Conventions

- **目录结构**：每个 skill 一个目录，至少含 `SKILL.md`；脚本放 `scripts/`，参考资料放 `references/`。
- **SKILL.md frontmatter**：保留 `name` / `version` / `description` 等字段；中文 skill 建议补 `description_zh` / `description_en`。
- **双语 README**：每个 skill 目录提供 `README.md`，结构统一为：简介 / 核心能力 / 适用场景 / 快速开始 / 安装 / 许可（中文 + English）。
- **脚本风格**：优先零第三方依赖（仅 Python 标准库），并提供 `--self-test` 便于回归。
- **许可**：未声明者默认 MIT；如引入其它许可请写在 skill 目录内。

## 如何贡献 / How to contribute

1. Fork 本仓库并新建分支 (`feat/...` 或 `fix/...`)。
2. 在对应 skill 目录内修改；如新增 skill，请补 `SKILL.md` 与双语 `README.md`，并在顶层 `README.md` / `README.en.md` 的组件表中登记。
3. 若为脚本改动，请跑通其 `--self-test`（如有的话）。
4. 提交 PR，简述改动与动机。

## 本地自检 / Local checks

```bash
# 例：跑某脚本的自测
python medical-literature-report/scripts/verify_report.py --self-test
```

## 行为准则 / Code of Conduct

保持友善、就事论事；不提交任何密钥、token 或个人隐私数据（见 `.gitignore`）。

---

Thanks for improving the bundle. Each skill lives in its own folder; keep READMEs bilingual and scripts dependency-light where possible.
