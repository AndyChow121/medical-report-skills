#!/usr/bin/env python3
"""
check_env.py - Verify required components for format-references-zotero skill.

Usage:
  python check_env.py            # check only
  python check_env.py --fix-ris  # check + fix .ris association to Zotero
"""

import sys
import subprocess
import ssl
import socket
import winreg
from pathlib import Path

# Bypass SSL certificate verification (corporate proxy SSL interception)
ssl._create_default_https_context = ssl._create_unverified_context

FIX_RIS = '--fix-ris' in sys.argv

PASS = '  ✓'
FAIL = '  ✗'
WARN = '  ⚠'

results = []

def check(label, passed=True, detail='', warn=False):
    symbol = WARN if warn else (PASS if passed else FAIL)
    line = f'{symbol}  {label}'
    if detail:
        line += f'\n       {detail}'
    print(line)
    results.append(True if (passed or warn) else False)


# ── Python ────────────────────────────────────────────────────────────────────
print('\n[ Python ]')
major, minor = sys.version_info[:2]
ok = (major, minor) >= (3, 7)
check(f'Python {major}.{minor}', ok,
      '' if ok else '需要 Python 3.7 或以上版本')


# ── python-docx ───────────────────────────────────────────────────────────────
print('\n[ python-docx ]')
try:
    import docx
    check('python-docx 已安装', True)
except ImportError:
    check('python-docx 未安装', False, '请运行: pip install python-docx')


# ── Pandoc ────────────────────────────────────────────────────────────────────
print('\n[ Pandoc ]')

def _find_pandoc():
    """Find Pandoc executable: PATH first, then file-level fallback."""
    # 1) Try PATH
    try:
        out = subprocess.check_output(['pandoc', '--version'],
                                      stderr=subprocess.DEVNULL, text=True)
        return ('pandoc', out.splitlines()[0])
    except FileNotFoundError:
        pass

    # 2) `where pandoc` (CMD built-in, often works when subprocess PATH fails)
    import os as _os
    candidates = []
    try:
        out = subprocess.check_output(
            ['cmd', '/c', 'where', 'pandoc'],
            stderr=subprocess.DEVNULL, text=True,
        )
        for line in out.strip().splitlines():
            p = Path(line.strip())
            if p.exists() and p.suffix == '.exe':
                candidates.append(p)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # 3) Known install locations (winget / Chocolatey / manual)
    for base in [
        Path(r'C:\Program Files\Pandoc'),
        Path(r'C:\Program Files (x86)\Pandoc'),
        Path(_os.environ.get('LOCALAPPDATA', '')) / 'Pandoc',
        Path(_os.environ.get('ProgramData', '')) / 'chocolatey' / 'bin',
    ]:
        exe = base / 'pandoc.exe'
        if exe.exists():
            candidates.append(exe)

    # 4) WinGet package directory (versioned subfolder, needs recursive glob)
    winget_root = Path(_os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'WinGet' / 'Packages'
    if winget_root.exists():
        for pkg in winget_root.glob('*Pandoc*'):
            for exe in pkg.rglob('pandoc.exe'):
                candidates.append(exe)

    # 5) `winget list` (Windows 10/11 built-in, finds anything installed via WinGet)
    try:
        out = subprocess.check_output(
            ['winget', 'list', '--id', 'JohnMacFarlane.Pandoc'],
            stderr=subprocess.DEVNULL, text=True,
        )
        for line in out.splitlines():
            if 'pandoc' in line.lower():
                p = Path(line.strip().rstrip('\\'))
                exe = p / 'pandoc.exe' if p.is_dir() else p
                if exe.exists() and exe.suffix == '.exe':
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
                [str(exe), '--version'],
                stderr=subprocess.DEVNULL, text=True,
            )
            return (str(exe), out.splitlines()[0])
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    return None

found = _find_pandoc()
if found:
    check(f'Pandoc 已安装 ({found[1]})', True, str(found[0]))
else:
    check('Pandoc 未找到', False, '请安装: https://pandoc.org/installing.html')

# ── PubMed API ────────────────────────────────────────────────────────────────
print('\n[ 网络 / PubMed API ]')
import urllib.request, urllib.error
try:
    url = ('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
           '?db=pubmed&id=33517359&retmode=xml')
    req = urllib.request.Request(url, headers={'User-Agent': 'check-env/1.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        check('PubMed API 可访问', resp.status == 200)
except Exception as e:
    check('PubMed API 无法访问', False, str(e))


# ── Zotero installed ──────────────────────────────────────────────────────────
print('\n[ Zotero ]')
zotero_exe = None

for hive_path in [r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                  r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall']:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, hive_path) as hive:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(hive, i)
                    with winreg.OpenKey(hive, sub) as key:
                        try:
                            name, _ = winreg.QueryValueEx(key, 'DisplayName')
                            if 'zotero' in name.lower():
                                try:
                                    loc, _ = winreg.QueryValueEx(key, 'InstallLocation')
                                    exe = Path(loc) / 'zotero.exe'
                                    if exe.exists():
                                        zotero_exe = exe
                                except (FileNotFoundError, OSError):
                                    pass
                        except (FileNotFoundError, OSError):
                            pass
                    i += 1
                except OSError:
                    break
    except OSError:
        continue
    if zotero_exe:
        break

# Fallback: common paths
if not zotero_exe:
    for base in [Path(r'C:\Program Files\Zotero'),
                 Path(r'C:\Program Files (x86)\Zotero')]:
        exe = base / 'zotero.exe'
        if exe.exists():
            zotero_exe = exe
            break

if zotero_exe:
    check('Zotero 已安装', True, str(zotero_exe))
else:
    check('未找到 Zotero', False, '请安装: https://www.zotero.org/download/')


# ── Zotero running (port 23119) ───────────────────────────────────────────────
print('\n[ Zotero 运行状态 ]')
try:
    s = socket.socket()
    s.settimeout(2)
    s.connect(('localhost', 23119))
    s.close()
    check('Zotero 正在运行（端口 23119 开放）', True,
          'Word 中 Refresh 时将正常格式化引用')
except OSError:
    check('Zotero 未运行', warn=True,
          detail='生成 .docx 不需要 Zotero 运行，但 Word 里 Refresh 时需要开着 Zotero')


# ── .ris 文件关联 ─────────────────────────────────────────────────────────────
print('\n[ .ris 文件关联 ]')

def set_ris_to_zotero(exe: Path):
    key_progid = r'SOFTWARE\Classes\ZoteroRISCustom'
    key_cmd    = r'SOFTWARE\Classes\ZoteroRISCustom\shell\open\command'
    key_ext    = r'SOFTWARE\Classes\.ris'
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_progid)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_progid,
                        access=winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, '', 0, winreg.REG_SZ, 'Zotero RIS')
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_cmd)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_cmd,
                        access=winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, '', 0, winreg.REG_SZ, f'"{exe}" "%1"')
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_ext)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_ext,
                        access=winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, '', 0, winreg.REG_SZ, 'ZoteroRISCustom')

try:
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r'.ris') as key:
        prog_id, _ = winreg.QueryValueEx(key, '')
    is_zotero = 'zotero' in prog_id.lower()
except (FileNotFoundError, OSError):
    prog_id = None
    is_zotero = False

if is_zotero:
    check(f'.ris 已关联到 Zotero ({prog_id})', True, '导入将自动触发')
elif FIX_RIS and zotero_exe:
    try:
        set_ris_to_zotero(zotero_exe)
        check('.ris 已关联到 Zotero（刚刚修改）', True, '导入将自动触发')
    except Exception as e:
        check(f'.ris 关联修改失败: {e}', False)
else:
    current = f'当前关联：{prog_id}' if prog_id else '当前无关联'
    check(f'.ris 未关联到 Zotero（{current}）', warn=True,
          detail='运行 check_env.py --fix-ris 可自动修复')


# ── 汇总 ──────────────────────────────────────────────────────────────────────
print('\n' + '─' * 50)
failed = results.count(False)
if failed == 0:
    print('✅ 环境检查通过，可以正常使用 format-references-zotero skill。')
else:
    print(f'❌ 发现 {failed} 个问题，请按上方提示修复后重试。')
print('─' * 50 + '\n')
