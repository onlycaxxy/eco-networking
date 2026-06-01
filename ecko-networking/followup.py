#!/usr/bin/env python3
"""
followup.py — 查看和管理待 follow-up 的聯絡人

用法:
  python followup.py          列出所有待 follow-up
  python followup.py done <id>  標記某人為已 follow-up
"""

import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ecko.db import NetworkingDB

console = Console()
db = NetworkingDB()
TODAY = datetime.now().strftime("%Y-%m-%d")


def list_followups() -> None:
    db.init()
    contacts = db.pending_followups()

    if not contacts:
        console.print(Panel.fit(
            "[green]✅  目前沒有待 follow-up 的聯絡人。[/green]",
            border_style="green",
        ))
        return

    # 分成逾期 / 今天 / 即將到來
    overdue  = [c for c in contacts if c.follow_up_by < TODAY]
    today    = [c for c in contacts if c.follow_up_by == TODAY]
    upcoming = [c for c in contacts if c.follow_up_by > TODAY]

    if overdue:
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold red")
        table.add_column("ID",      width=4)
        table.add_column("姓名",    width=14)
        table.add_column("聯絡方式", width=22)
        table.add_column("Deadline", width=12)
        table.add_column("備註",    width=28)
        for c in overdue:
            table.add_row(
                str(c.id), c.name, c.contact or "—",
                f"[red]{c.follow_up_by}[/red]", c.notes[:26] or "—",
            )
        console.print(Panel(table, title="[red]⚠️  逾期 Follow-up[/red]", border_style="red"))

    if today:
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold yellow")
        table.add_column("ID",      width=4)
        table.add_column("姓名",    width=14)
        table.add_column("聯絡方式", width=22)
        table.add_column("備註",    width=28)
        for c in today:
            table.add_row(str(c.id), c.name, c.contact or "—", c.notes[:26] or "—")
        console.print(Panel(table, title="[yellow]📬  今天要 Follow-up[/yellow]", border_style="yellow"))

    if upcoming:
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        table.add_column("ID",      width=4)
        table.add_column("姓名",    width=14)
        table.add_column("聯絡方式", width=22)
        table.add_column("Deadline", width=12)
        for c in upcoming:
            table.add_row(str(c.id), c.name, c.contact or "—", c.follow_up_by)
        console.print(Panel(table, title="[cyan]🗓️  即將到來[/cyan]", border_style="cyan"))

    console.print(f"  標記完成：[cyan]python followup.py done <ID>[/cyan]\n")


def mark_done(contact_id: int) -> None:
    db.init()
    contacts = db.list_contacts()
    target   = next((c for c in contacts if c.id == contact_id), None)

    if not target:
        console.print(f"[red]❌  找不到聯絡人 ID {contact_id}。[/red]")
        sys.exit(1)

    db.mark_followup_done(contact_id)
    console.print(f"[green]✅  已標記完成：{target.name}[/green]")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        list_followups()
    elif args[0] == "done" and len(args) > 1:
        try:
            mark_done(int(args[1]))
        except ValueError:
            console.print("[red]❌  ID 必須是數字。[/red]")
    else:
        print(__doc__)
