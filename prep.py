#!/usr/bin/env python3
"""
prep.py — 生成活動準備包

呼叫 Claude API，根據你的第二大腦內容和活動資訊，
生成個人化的 Markdown 準備包。

用法: python prep.py <event_id>
"""

import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich import print as rprint

from ecko.db import NetworkingDB
from ecko.llm import PrepGenerator
from setup import load_config

console = Console()
db = NetworkingDB()

PREP_DIR = Path(__file__).parent / "prep"

STATIC_FOOTER = """
---

## 🚨 焦慮應急包（固定版）

- 提早 10 分鐘到，先站角落觀察，讓空間先熟悉你
- 手機鬧鐘設 45 分鐘，到了就有正當理由離開
- 如果沉默超過 5 秒，問「你最近在忙什麼？」——永遠有效
- **退場許可：** 你不需要解釋為什麼要走

---

## 📝 事後記錄

活動結束後執行：`python checkin.py {event_id}`

"""


def generate(event_id: int) -> None:
    db.init()

    event = db.get_event(event_id)
    if not event:
        console.print(f"[red]❌  找不到活動 ID {event_id}。執行 python list.py 查看。[/red]")
        sys.exit(1)

    config = load_config()

    # 從第二大腦讀入所有素材
    brain_entries = {
        "pitch":       db.get_brain("pitch"),
        "intro":       db.get_brain("intro"),
        "insight":     db.get_brain("insight"),
        "anxiety_tip": db.get_brain("anxiety_tip"),
    }

    has_brain = any(brain_entries.values())
    if not has_brain:
        console.print("[yellow]⚠️  第二大腦是空的。建議先執行 python brain.py add pitch[/yellow]")
        console.print("[yellow]   準備包仍會生成，但內容會比較通用。[/yellow]\n")

    # 呼叫 Claude API
    event_label = "Coffee Chat" if event.type == "coffee_chat" else "小型聚會"
    console.print(Panel.fit(
        f"[bold]{event.name}[/bold]\n"
        f"📅 {event.datetime}  ｜  📍 {event.location or '（未填）'}  ｜  {event_label}",
        border_style="cyan",
    ))

    with console.status("[cyan]正在用 Claude 生成個人化準備包...[/cyan]", spinner="dots"):
        generator = PrepGenerator(config)
        ai_content = generator.generate(event, brain_entries)

    # 組裝完整 Markdown
    header = (
        f"# 準備包：{event.name}\n"
        f"> 📅 **{event.datetime}**　｜　📍 {event.location or '（未填）'}　｜　{event_label}\n"
    )
    if event.url:
        header += f"> 🔗 {event.url}\n"
    header += f"> 🤖 生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n"

    full_content = header + ai_content + STATIC_FOOTER.format(event_id=event_id)

    # 寫出檔案
    safe_name = event.name.replace(" ", "-").replace("/", "-")
    date_str  = event.datetime[:10]
    out_path  = PREP_DIR / f"{date_str}-{safe_name}.md"
    out_path.write_text(full_content, encoding="utf-8")

    console.print(f"\n[green]✅  準備包已生成[/green]")
    console.print(f"   [dim]{out_path}[/dim]")
    console.print(f"\n   用 VS Code 開啟：[cyan]code \"{out_path}\"[/cyan]")
    console.print(f"   活動後記錄：    [cyan]python checkin.py {event_id}[/cyan]\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    try:
        generate(int(sys.argv[1]))
    except ValueError:
        console.print("[red]❌  event_id 必須是數字。[/red]")
        sys.exit(1)
