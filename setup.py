#!/usr/bin/env python3
"""
setup.py — 第一次執行，設定個人資料和 Claude API key

用法: python setup.py
"""

from pathlib import Path
import yaml
from rich.console import Console
from rich.panel import Panel

console = Console()
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def run_setup() -> None:
    console.print(Panel.fit(
        "[bold]Ecko Networking System — 初始設定[/bold]\n"
        "只需要做一次，之後所有腳本自動讀取。",
        border_style="cyan",
    ))

    console.print("\n[bold cyan]你的基本資料[/bold cyan]")
    name    = input("你的名字：").strip() or "Cathy"
    product = input("產品名稱：").strip() or "Ecko"
    tagline = input("產品一句話介紹：").strip() or "AI journal app，幫助焦慮的思考者找回聲音"

    console.print("\n[bold cyan]Claude API[/bold cyan]")
    console.print("取得 API key：[link]https://console.anthropic.com[/link]")
    api_key = input("API Key (sk-ant-...)：").strip()

    if not api_key.startswith("sk-"):
        console.print("[yellow]⚠️  API key 格式看起來不對，但還是會幫你存下來。[/yellow]")

    config = {
        "user": {
            "name":    name,
            "product": product,
            "tagline": tagline,
        },
        "claude": {
            "api_key": api_key,
            "model":   "claude-haiku-4-5-20251001",
        },
    }

    CONFIG_PATH.write_text(yaml.dump(config, allow_unicode=True), encoding="utf-8")

    console.print(f"\n[green]✅  設定完成，已存到 config.yaml[/green]")
    console.print("\n下一步：")
    console.print("  [cyan]python brain.py add pitch[/cyan]   ← 填入你的 pitch")
    console.print("  [cyan]python brain.py add intro[/cyan]   ← 填入自我介紹")
    console.print("  [cyan]python add_event.py[/cyan]         ← 新增第一個活動\n")


def load_config():
    """讀取 config.yaml，回傳 UserConfig。供其他腳本使用。"""
    from ecko.models import UserConfig

    if not CONFIG_PATH.exists():
        console.print("[red]❌  找不到 config.yaml。請先執行 python setup.py[/red]")
        raise SystemExit(1)

    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return UserConfig(
        name    = raw["user"]["name"],
        product = raw["user"]["product"],
        tagline = raw["user"]["tagline"],
        api_key = raw["claude"]["api_key"],
        model   = raw["claude"].get("model", "claude-haiku-4-5-20251001"),
    )


if __name__ == "__main__":
    run_setup()
