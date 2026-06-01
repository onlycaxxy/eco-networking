#!/usr/bin/env python3
"""
checkin.py — 活動後記錄

記錄遇到誰、聊了什麼、要不要 follow-up。

用法: python checkin.py <event_id>
"""

import sys
from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel

from ecko.db import NetworkingDB

console = Console()
db = NetworkingDB()


def ask(prompt: str) -> str:
    console.print(f"  {prompt}", end=" ")
    return input().strip()


def checkin(event_id: int) -> None:
    db.init()

    event = db.get_event(event_id)
    if not event:
        console.print(f"[red]❌  找不到活動 ID {event_id}。[/red]")
        sys.exit(1)

    console.print(Panel.fit(
        f"[bold]活動後記錄[/bold]\n{event.name}  ｜  {event.datetime}",
        border_style="cyan",
    ))

    # ── 記錄遇到的人 ──────────────────────────────────────────────────────────
    console.print("\n[bold cyan]你今天遇到了誰？[/bold cyan]  （名字留空跳過）\n")
    contact_count = 0

    while True:
        name = ask("姓名：")
        if not name:
            break

        role    = ask("他在做什麼（可留空）：")
        contact = ask("聯絡方式 email / LinkedIn（可留空）：")
        notes   = ask("聊了什麼值得記？：")

        # Follow-up
        console.print("  要 follow-up 嗎？", end=" ")
        fu_input = input().strip().lower()
        follow_up_by = None

        if fu_input in ("y", "yes", "是", "要"):
            console.print("  幾天內？[dim]（預設 3）[/dim]", end=" ")
            days_str = input().strip()
            days = int(days_str) if days_str.isdigit() else 3
            follow_up_by = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            console.print(f"  [dim]→ follow-up deadline：{follow_up_by}[/dim]")

        db.add_contact(
            event_id=event_id, name=name, role=role,
            contact=contact, notes=notes, follow_up_by=follow_up_by,
        )
        contact_count += 1
        console.print(f"  [green]✅  已記錄：{name}[/green]\n")

    # ── 記錄 Takeaway ─────────────────────────────────────────────────────────
    console.print("[bold cyan]這次的 takeaway[/bold cyan]  （留空結束）\n")
    takeaway_count = 0

    while True:
        content = ask("Takeaway：")
        if not content:
            break
        db.add_takeaway(event_id=event_id, content=content)
        takeaway_count += 1

    # ── 結束摘要 ──────────────────────────────────────────────────────────────
    pending = len([c for c in db.list_contacts(event_id) if c.follow_up_by])

    console.print(Panel.fit(
        f"[green]記錄完成[/green]\n\n"
        f"  新增聯絡人：{contact_count} 人\n"
        f"  Takeaway：{takeaway_count} 筆\n"
        f"  待 follow-up：{pending} 人",
        border_style="green",
    ))

    if pending:
        console.print(f"\n  查看所有待 follow-up：[cyan]python followup.py[/cyan]\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    try:
        checkin(int(sys.argv[1]))
    except ValueError:
        console.print("[red]❌  event_id 必須是數字。[/red]")
        sys.exit(1)
