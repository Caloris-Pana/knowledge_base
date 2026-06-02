"""Knowledge Base deployment script.

Usage:
    python setup.py              # interactive (prompt before overwrites)
    python setup.py --yes         # skip all prompts
    python setup.py --dry-run     # preview only, no changes
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

# ── paths ───────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(ROOT, "chroma_db")
SKILL_SRC = os.path.join(ROOT, "config", "SKILL.md")
SKILL_DST_DIR = os.path.join(ROOT, ".opencode", "skills", "knowledge-base")
SKILL_DST = os.path.join(SKILL_DST_DIR, "SKILL.md")
MCP_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "opencode")
MCP_CONFIG_PATH = os.path.join(MCP_CONFIG_DIR, "opencode.jsonc")


# ── helpers ─────────────────────────────────────────────────────────────

def info(msg: str):
    print(f"  ✓  {msg}")


def warn(msg: str):
    print(f"  !  {msg}")


def dry_info(msg: str):
    print(f"  ~  {msg}")


def ask_yes_no(prompt: str) -> bool:
    while True:
        ans = input(f"  ?  {prompt} [y/N] ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("", "n", "no"):
            return False


def run(cmd: list[str], desc: str, dry_run: bool):
    if dry_run:
        dry_info(f"{desc}: {' '.join(cmd)}")
        return True
    print(f"  ⏳  {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗  {desc} failed (exit {result.returncode})")
        print(result.stderr[:500])
        return False
    info(f"{desc}")
    return True


# ── steps ───────────────────────────────────────────────────────────────

def step_check_python(yes: bool, dry_run: bool) -> bool:
    if sys.version_info < (3, 10):
        print(f"  ✗  Python >= 3.10 required (got {sys.version})")
        return False
    if dry_run:
        dry_info(f"Check Python >= 3.10: {sys.version}")
    else:
        info(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def step_install_deps(yes: bool, dry_run: bool) -> bool:
    uv_path = shutil.which("uv")
    if uv_path:
        return run(
            [uv_path, "pip", "install", "-r", os.path.join(ROOT, "requirements.txt")],
            "安装依赖 (via uv)",
            dry_run,
        )

    pip_check = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True, text=True,
    )
    if pip_check.returncode != 0:
        print("  ✗  当前环境既无 uv 也无 pip，无法安装依赖")
        print("      请执行以下任一命令后重试：")
        print("        winget install uv    # Windows")
        print("        pip install -r requirements.txt   # 先确保 pip 可用")
        return False

    return run(
        [sys.executable, "-m", "pip", "install", "-r", os.path.join(ROOT, "requirements.txt")],
        "安装依赖 (via pip)",
        dry_run,
    )


def step_deploy_skill(yes: bool, dry_run: bool) -> bool:
    if not os.path.isfile(SKILL_SRC):
        warn(f"未找到 SKILL.md 源文件: {SKILL_SRC}")
        return True

    if os.path.isfile(SKILL_DST):
        if dry_run:
            dry_info(f"覆盖 .opencode/skills/knowledge-base/SKILL.md")
            return True
        if not yes and not ask_yes_no("覆盖已存在的 SKILL.md？"):
            warn("跳过 SKILL.md 部署")
            return True

    if dry_run:
        dry_info(f"复制 SKILL.md → {SKILL_DST}")
        return True

    os.makedirs(SKILL_DST_DIR, exist_ok=True)
    shutil.copy2(SKILL_SRC, SKILL_DST)
    info("部署 SKILL.md -> .opencode/skills/knowledge-base/")
    return True


def step_gen_mcp_config(yes: bool, dry_run: bool) -> bool:
    if dry_run:
        dry_info("生成 ~/.config/opencode/opencode.jsonc")
        _show_mcp_preview()
        return True

    os.makedirs(MCP_CONFIG_DIR, exist_ok=True)

    # read existing config (or start fresh)
    config: dict = {}
    if os.path.isfile(MCP_CONFIG_PATH):
        try:
            with open(MCP_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError):
            warn(f"无法解析 {MCP_CONFIG_PATH}，将创建新文件（原文件被备份）")
            bak = MCP_CONFIG_PATH + ".bak"
            shutil.copy2(MCP_CONFIG_PATH, bak)
            info(f"已备份原文件到 {bak}")
            config = {}

    if "$schema" not in config:
        config["$schema"] = "https://opencode.ai/config.json"

    python_path = sys.executable
    script_path = os.path.join(ROOT, "src", "kb_server.py")

    knowledge_base_config = {
        "type": "local",
        "command": [
            python_path,
            script_path,
        ],
        "timeout": 60000,
    }

    if "mcp" not in config:
        config["mcp"] = {}
    config["mcp"]["knowledge-base"] = knowledge_base_config

    with open(MCP_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")

    info("生成 ~/.config/opencode/opencode.jsonc")
    _show_mcp_preview()
    return True


def _show_mcp_preview():
    python_path = sys.executable
    script_path = os.path.join(ROOT, "src", "kb_server.py")
    print(f"       Python: {python_path}")
    print(f"       Script: {script_path}")


def step_init_kb(yes: bool, dry_run: bool) -> bool:
    if dry_run:
        dry_info("初始化 chroma_db/ 知识库")
        return True

    # inject ROOT into sys.path so scripts/ can be imported
    sys.path.insert(0, ROOT)

    from scripts.query import get_collection

    try:
        get_collection()
        info(f"初始化知识库成功: {CHROMA_DIR}")
    except Exception as e:
        warn(f"初始化知识库失败: {e}")
        return False

    return True


def step_warmup_model(yes: bool, dry_run: bool) -> bool:
    """预热嵌入模型，消除首次 save_solution / search_solutions 的延迟"""
    if dry_run:
        dry_info("预热嵌入模型 all-MiniLM-L6-v2")
        return True

    sys.path.insert(0, ROOT)
    from scripts.model import get_model

    try:
        get_model()
        info("嵌入模型预热完成")
    except Exception as e:
        warn(f"嵌入模型预热失败: {e}")
        return True

    return True


# ── main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Deploy knowledge base for opencode")
    parser.add_argument("--yes", action="store_true", help="skip all confirmation prompts")
    parser.add_argument("--dry-run", action="store_true", help="preview actions without making changes")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print(f"\n{'='*50}")
    print("  Knowledge Base — 部署脚本")
    print(f"{'='*50}\n")

    steps = [
        ("检查 Python 版本", step_check_python),
        ("安装依赖", step_install_deps),
        ("部署 SKILL.md", step_deploy_skill),
        ("生成 MCP 配置", step_gen_mcp_config),
        ("初始化知识库", step_init_kb),
        ("预热嵌入模型", step_warmup_model),
    ]

    ok = True
    for label, fn in steps:
        print(f"\n[{label}]")
        if not fn(args.yes, args.dry_run):
            print(f"  ✗ 步骤失败: {label}")
            ok = False
            break

    print()
    if args.dry_run:
        print("⚠  预览模式，未做任何更改")
    elif ok:
        print("✅ 部署完成！")
        print(f"   启动 opencode 后即可使用知识库工具:\n"
              f"      list_solutions  |  search_solutions\n"
              f"      get_solution    |  save_solution\n"
              f"      delete_solution")
    else:
        print("❌ 部署未完成，请检查上方错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
