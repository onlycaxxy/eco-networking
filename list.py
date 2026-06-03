#!/usr/bin/env python3
"""
list.py — 查看活動、聯絡人、takeaway

用法:
  python list.py                        查看即將到來的活動
  python list.py events                 查看所有活動（含過去）
  python list.py contacts               查看所有聯絡人
  python list.py contacts <event_id>    查看某場活動的聯絡人
  python list.py takeaways <event_id>   查看某場活動的 takeaway
"""

import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ecko.db import NetworkingDB

console = Console()
db = NetworkingDB()


def list_events(all_: bool = False) -> None:
    events = db.list_events(upcoming_only=not all_)
    label  = "所有活動" if all_ else "即將到來的活動"

    if not events:
        console.print(f"\n📭  沒有{label}。執行 [cyan]python add_event.py[/cyan] 新增。\n")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("ID",   width=4,  justify="right")
    table.add_column("名稱", min_width=22)
    table.add_column("類型", width=12)
    table.add_column("時間", width=16)
    table.add_column("地點", min_width=16)

    for e in events:
        label_ = "Coffee Chat" if e.type == "coffee_chat" else "小型聚會"
        table.add_row(str(e.id), e.name, label_, e.datetime, e.location or "—")

    console.print(Panel(table, title=f"[bold]{label}（{len(events)} 筆）[/bold]", border_style="cyan"))


def list_contacts(event_id: "int | None" = None) -> None:
    contacts = db.list_contacts(event_id)
    title    = f"活動 {event_id} 的聯絡人" if event_id else "所有聯絡人"

    if not contacts:
        console.print(f"\n📭  {title}：尚無記錄。\n")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("ID",      width=4,  justify="right")
    table.add_column("姓名",    width=14)
    table.add_column("職稱",    width=16)
    table.add_column("聯絡方式", width=22)
    table.add_column("Follow-up", width=12)
    table.add_column("備註",    min_width=20)

    for c in contacts:
        if c.follow_up_done:
            fu = "[dim]✅ 完成[/dim]"
        elif c.follow_up_by:
            fu = f"[yellow]{c.follow_up_by}[/yellow]"
        else:
            fu = "—"
        table.add_row(str(c.id), c.name, c.role or "—", c.contact or "—", fu, c.notes[:20] or "—")

    console.print(Panel(table, title=f"[bold]{title}（{len(contacts)} 人）[/bold]", border_style="cyan"))


def list_takeaways(event_id: int) -> None:
    event     = db.get_event(event_id)
    takeaways = db.list_takeaways(event_id)

    if not event:
        console.print(f"[red]❌  找不到活動 ID {event_id}。[/red]")
        return
    if not takeaways:
        console.print(f"\n📭  {event.name} 還沒有 takeaway 記錄。\n")
        return

    console.print(f"\n[bold cyan]── {event.name} 的 Takeaway ──[/bold cyan]\n")
    for t in takeaways:
        console.print(f"  • {t.content}")
    console.print()


def main() -> None:
    db.init()
    args = sys.argv[1:]

    if not args or args[0] == "events":
        list_events(all_=bool(args))
    elif args[0] == "contacts":
        eid = int(args[1]) if len(args) > 1 else None
        list_contacts(eid)
    elif args[0] == "takeaways":
        if len(args) < 2:
            console.print("用法：python list.py takeaways <event_id>")
            sys.exit(1)
        list_takeaways(int(args[1]))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
