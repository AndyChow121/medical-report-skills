#!/usr/bin/env python3
"""
check_env.py - Verify required components for the format-references (EndNote) skill.

Usage: python check_env.py
"""

import sys
import subprocess
import ssl
import urllib.request
import urllib.error
import winreg
from pathlib import Path

# Bypass SSL certificate verification (corporate proxy SSL interception)
ssl._create_default_https_context = ssl._create_unverified_context

FIX_RIS = "--fix-ris" in sys.argv

PASS = "  ✓"
FAIL = "  ✗"
WARN = "  ⚠"

results = []

def check(label, passed=True, detail="", warn=False):
    symbol = WARN if warn else (PASS if passed else FAIL)
    line = f"{symbol}  {label}"
    if detail:
        line += f"\n       {detail}"
    print(line)
    results.append(True if (passed or warn) else False)


# ── Python ────────────────────────────────────────────────────────────────────
print("\n[ Python ]")
major, minor = sys.version_info[:2]
ok = (major, minor) >= (3, 7)
check(f"Python {major}.{minor}", ok,
      "" if ok else "需要 Python 3.7 或以上版本")


# ── Pandoc ────────────────────────────────────────────────────────────────────
print("\n[ Pandoc ]")

def _find_pandoc():
    """Find Pandoc executable: PATH first, then file-level fallback."""
    # 1) Try PATH
    try:
        out = subprocess.check_output(["pandoc", "--version"],
                                      stderr=subprocess.DEVNULL, text=True)
        return ("pandoc", out.splitlines()[0])
    except FileNotFoundError:
        pass

    # 2) `where pandoc` (CMD built-in, often works when subprocess PATH fails)
    import os as _os
    candidates = []
    try:
        out = subprocess.check_output(
            ["cmd", "/c", "where", "pandoc"],
            stderr=subprocess.DEVNULL, text=True,
        )
        for line in out.strip().splitlines():
            p = Path(line.strip())
            if p.exists() and p.suffix == ".exe":
                candidates.append(p)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # 3) Known install locations (winget / Chocolatey / manual)
    for base in [
        Path(r"C:\Program Files\Pandoc"),
        Path(r"C:\Program Files (x86)\Pandoc"),
        Path(_os.environ.get("LOCALAPPDATA", "")) / "Pandoc",
        Path(_os.environ.get("ProgramData", "")) / "chocolatey" / "bin",
    ]:
        exe = base / "pandoc.exe"
        if exe.exists():
            candidates.append(exe)

    # 4) WinGet package directory (versioned subfolder, needs recursive glob)
    winget_root = Path(_os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if winget_root.exists():
        for pkg in winget_root.glob("*Pandoc*"):
            for exe in pkg.rglob("pandoc.exe"):
                candidates.append(exe)

    # 5) `winget list` (Windows 10/11 built-in, finds anything installed via WinGet)
    try:
        out = subprocess.check_output(
            ["winget", "list", "--id", "JohnMacFarlane.Pandoc"],
            stderr=subprocess.DEVNULL, text=True,
        )
        # winget output lines contain the install path; scan for .exe
        for line in out.splitlines():
            if "pandoc" in line.lower():
                p = Path(line.strip().rstrip("\\"))
                exe = p / "pandoc.exe" if p.is_dir() else p
                if exe.exists() and exe.suffix == ".exe":
                    candidates.append(exe)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Deduplicate and test
    seen = set()
    for exe in candidates:
        key = str(exe.resolve())
        if key in seen:
            continue
        seen.add(key)
        try:
            out = subprocess.check_output(
                [str(exe), "--version"],
                stderr=subprocess.DEVNULL, text=True,
            )
            return (str(exe), out.splitlines()[0])
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    return None

found = _find_pandoc()
if found:
    check(f"Pandoc 已安装 ({found[1]})", True, str(found[0]))
else:
    check("Pandoc 未找到", False,
          "请安装: https://pandoc.org/installing.html")


# ── PubMed API ────────────────────────────────────────────────────────────────
print("\n[ 网络 / PubMed API ]")
try:
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
           "?db=pubmed&id=33517359&retmode=xml")
    req = urllib.request.Request(url, headers={"User-Agent": "check-env/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        check("PubMed API 可访问", resp.status == 200)
except Exception as e:
    check("PubMed API 无法访问", False, str(e))


# ── EndNote ───────────────────────────────────────────────────────────────────
print("\n[ EndNote ]")

endnote_exe = None

# 从标准 Windows 卸载列表里找 EndNote（支持任意安装盘符）
for hive_path in [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                  r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, hive_path) as hive:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(hive, i)
                    with winreg.OpenKey(hive, sub) as key:
                        try:
                            name, _ = winreg.QueryValueEx(key, "DisplayName")
                            if "endnote" in name.lower():
                                loc, _ = winreg.QueryValueEx(key, "InstallLocation")
                                exe = Path(loc) / "EndNote.exe"
                                if exe.exists():
                                    endnote_exe = exe
                        except (FileNotFoundError, OSError):
                            pass
                    i += 1
                except OSError:
                    break
    except OSError:
        continue
    if endnote_exe:
        break

if endnote_exe:
    check(f"EndNote 已安装", True, str(endnote_exe))
else:
    check("未找到 EndNote.exe", False,
          "请安装 EndNote: https://endnote.com")


# ── .ris 文件关联 ─────────────────────────────────────────────────────────────
print("\n[ .ris 文件关联 ]")

def set_ris_to_endnote(exe: Path):
    """将 .ris 关联到 EndNote（写用户级注册表，不影响其他用户）。"""
    key_progid = r"SOFTWARE\Classes\EndNoteRIS"
    key_cmd    = r"SOFTWARE\Classes\EndNoteRIS\shell\open\command"
    key_ext    = r"SOFTWARE\Classes\.ris"
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_progid)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_progid, access=winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "EndNote Reference")
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_cmd)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_cmd, access=winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'"{exe}" "%1"')
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_ext)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_ext, access=winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "EndNoteRIS")

try:
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r".ris") as key:
        prog_id, _ = winreg.QueryValueEx(key, "")
    is_endnote = "endnote" in prog_id.lower()
except (FileNotFoundError, OSError):
    prog_id = None
    is_endnote = False

if is_endnote:
    check(f".ris 已关联到 EndNote ({prog_id})", True, "导入将自动触发")
elif FIX_RIS and endnote_exe:
    try:
        set_ris_to_endnote(endnote_exe)
        check(".ris 已关联到 EndNote（刚刚修改）", True, "导入将自动触发")
    except Exception as e:
        check(f".ris 关联修改失败: {e}", False)
else:
    current = f"当前关联：{prog_id}" if prog_id else "当前无关联"
    check(f".ris 未关联到 EndNote（{current}）", warn=True,
          detail="运行 check_env.py --fix-ris 可自动修复")


# ── 汇总 ──────────────────────────────────────────────────────────────────────
print("\n" + "─" * 50)
failed = results.count(False)
if failed == 0:
    print("✅ 环境检查通过，可以正常使用 format-references skill。")
else:
    print(f"❌ 发现 {failed} 个问题，请按上方提示修复后重试。")
print("─" * 50 + "\n")
