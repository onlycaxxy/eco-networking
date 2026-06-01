#!/usr/bin/env python3
"""
add_event.py — 新增活動

支援兩種類型：
  meetup     小型聚會（5–30 人）
  coffee_chat  1 on 1 對談

用法: python add_event.py
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from rich.console import Console
from rich.panel import Panel

from ecko.db import NetworkingDB

console = Console()
db = NetworkingDB()
TZ = ZoneInfo("Asia/Taipei")


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [dim]（{default}）[/dim]" if default else ""
    console.print(f"  {prompt}{suffix}", end=" ")
    val = input().strip()
    return val or default


def add_event() -> None:
    db.init()

    console.print(Panel.fit(
        "[bold]新增活動[/bold]",
        border_style="cyan",
    ))

    # 類型選擇
    console.print("\n  活動類型：")
    console.print("  [cyan][1][/cyan] 小型聚會 meetup")
    console.print("  [cyan][2][/cyan] Coffee chat（1 on 1）")
    choice = input("  選擇 (1/2)：").strip()
    type_  = "coffee_chat" if choice == "2" else "meetup"

    console.print()
    name     = ask("活動名稱 / 對方姓名：")
    if not name:
        console.print("[red]❌  名稱不能為空。[/red]")
        return

    while True:
        dt_str = ask("時間（YYYY-MM-DD HH:MM）：")
        try:
            datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            break
        except ValueError:
            console.print("  [yellow]格式不對，例如：2026-05-30 10:00[/yellow]")

    location = ask("地點（可留空）：")
    url      = ask("活動連結（可留空）：")

    if type_ == "meetup":
        notes = ask("備註，例如參加者輪廓（可留空）：")
    else:
        notes = ask("對方的背景 / 你們怎麼認識的（可留空）：")

    event_id = db.add_event(
        name=name, datetime=dt_str, type_=type_,
        location=location, url=url, notes=notes,
    )

    dt      = datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
    prep_at = (dt - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
    label   = "Coffee Chat" if type_ == "coffee_chat" else "小型聚會"

    console.print(f"\n[green]✅  已新增（ID {event_id}）[/green]")
    console.print(f"   {name}  ｜  {dt_str}  ｜  {label}")
    console.print(f"\n   建議在 [bold]{prep_at}[/bold] 執行：")
    console.print(f"   [cyan]python prep.py {event_id}[/cyan]\n")


if __name__ == "__main__":
    add_event()
