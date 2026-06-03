#!/usr/bin/env python3
"""
setup.py — 第一次執行，設定個人資料和 Claude API key

用法: python setup.py
"""

from pathlib import Path
import yaml
from openai import OpenAI, AuthenticationError  # noqa: F401
from rich.console import Console
from rich.panel import Panel

console = Console()
CONFIG_PATH = Path(__file__).parent / "config.yaml"

# ── 已知 supplier 預設值 ──────────────────────────────────────────────────────

SUPPLIERS = {
    "1": {
        "name":     "Anthropic（官方）",
        "base_url": "https://api.anthropic.com/v1",
        "model":    "claude-haiku-4-5-20251001",
    },
    "2": {
        "name":     "Aliyun DashScope（通用）",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model":    "qwen-plus",
    },
    "3": {
        "name":     "Aliyun MaaS（私有 workspace endpoint）",
        "base_url": "",   # 每個 workspace URL 不同，需手動填
        "model":    "qwen3.7-plus",
    },
    "4": {
        "name":     "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "model":    "llama-3.3-70b-versatile",
    },
    "5": {
        "name":     "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "model":    "anthropic/claude-haiku",
    },
    "6": {
        "name":     "自訂",
        "base_url": "",
        "model":    "",
    },
}


def run_setup() -> None:
    console.print(Panel.fit(
        "[bold]Ecko Networking System — 初始設定[/bold]\n"
        "只需要做一次，之後所有腳本自動讀取。",
        border_style="cyan",
    ))

    # ── 個人資料 ──────────────────────────────────────────────────────────────
    console.print("\n[bold cyan]你的基本資料[/bold cyan]")
    name    = input("你的名字：").strip() or "Cathy"
    product = input("產品名稱：").strip() or "Ecko"
    tagline = input("產品一句話介紹：").strip() or "AI journal app，幫助焦慮的思考者找回聲音"

    # ── Supplier 選擇 ─────────────────────────────────────────────────────────
    console.print("\n[bold cyan]API Supplier[/bold cyan]")
    for key, s in SUPPLIERS.items():
        console.print(f"  [cyan][{key}][/cyan] {s['name']}")
    choice = input("選擇 (1–6)：").strip() or "1"
    supplier = SUPPLIERS.get(choice, SUPPLIERS["1"])

    if choice in ("3", "6") or not supplier["base_url"]:
        supplier["base_url"] = input("Base URL（例：https://ws-xxx.maas.aliyuncs.com/compatible-mode/v1）：").strip()
    if choice == "5":
        supplier["model"] = input("預設模型名稱：").strip()

    console.print(f"  → [dim]{supplier['base_url']}[/dim]")

    # ── API Key ───────────────────────────────────────────────────────────────
    console.print("\n[bold cyan]API Key[/bold cyan]")
    api_key = input("API Key：").strip()

    # ── 自訂模型（可選）──────────────────────────────────────────────────────
    console.print(f"\n[bold cyan]模型名稱[/bold cyan]  [dim]（留空使用預設：{supplier['model']}）[/dim]")
    model_input = input("模型：").strip()
    model = model_input or supplier["model"]

    # ── 存檔 ─────────────────────────────────────────────────────────────────
    config = {
        "user": {
            "name":    name,
            "product": product,
            "tagline": tagline,
        },
        "claude": {
            "supplier": supplier["name"],
            "base_url": supplier["base_url"],
            "api_key":  api_key,
            "model":    model,
        },
    }
    CONFIG_PATH.write_text(yaml.dump(config, allow_unicode=True), encoding="utf-8")

    # ── 驗證 API key（使用 models.list，不依賴特定模型名稱）─────────────────
    console.print("\n[dim]驗證 API key...[/dim]", end=" ")
    try:
        client = OpenAI(api_key=api_key, base_url=supplier["base_url"])
        client.models.list()
        console.print("[green]✅[/green]")
    except AuthenticationError:
        console.print(
            "[yellow]⚠️  API key 驗證未通過（401）。"
            "設定已存檔，但請確認 key 正確後再執行 prep.py。[/yellow]"
        )
    except Exception as e:
        console.print(f"[yellow]⚠️  無法驗證（{e}），請確認網路和 base_url 後繼續。[/yellow]")

    # ── 完成 ──────────────────────────────────────────────────────────────────
    console.print(f"\n[green]✅  設定完成，已存到 config.yaml[/green]")
    console.print("\n下一步：")
    console.print("  [cyan]python brain.py add pitch[/cyan]   ← 填入你的 pitch")
    console.print("  [cyan]python brain.py add intro[/cyan]   ← 填入自我介紹")
    console.print("  [cyan]python add_event.py[/cyan]         ← 新增第一個活動\n")


def load_config():
    """讀取 config.yaml，回傳 UserConfig。供其他腳本使用。"""
    import os
    from ecko.models import UserConfig

    if not CONFIG_PATH.exists():
        console.print("[red]❌  找不到 config.yaml。請先執行 python setup.py[/red]")
        raise SystemExit(1)

    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

    # API key：config.yaml 優先，fallback 到環境變數
    api_key = (raw["claude"].get("api_key") or "").strip()
    if not api_key:
        api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("OPENAI_API_KEY", "")

    return UserConfig(
        name     = raw["user"]["name"],
        product  = raw["user"]["product"],
        tagline  = raw["user"]["tagline"],
        api_key  = api_key,
        model    = raw["claude"].get("model", "qwen-plus"),
        base_url = raw["claude"].get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    )


if __name__ == "__main__":
    run_setup()
