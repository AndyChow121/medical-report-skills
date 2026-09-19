"""pytest 配置：把 scripts/ 加入 sys.path。

graph-interpretation 的模块位于 scripts/ 下，且彼此以顶层模块方式 import
（如 `from parsers import PARSERS`、`from _schema import ...`），
因此测试运行前必须把 scripts/ 放进 sys.path，而不是依赖包结构。

这让 tests/ 既能在本仓库跑（pytest tests/），也能在 pip 安装态下
指向 site-packages 里的 scripts 包。
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
