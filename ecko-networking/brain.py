#!/usr/bin/env python3
"""
brain.py — 管理你的第二大腦

用法:
  python brain.py add <type>      新增條目
  python brain.py edit <id>       編輯現有條目
  python brain.py list            列出所有條目
  python brain.py list <type>     列出某類型
  python brain.py off <id>        封存
  python brain.py on  <id>        重新啟用

type 可以是:
  pitch        Ecko 的 marketing pitch
  intro        自我介紹版本
  insight      個人洞察 / 破冰話題素材
  anxiety_tip  焦慮應對策略
"""

import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ecko.db import NetworkingDB

console = Console()
db = NetworkingDB()

VALID_TYPES = ("pitch", "intro", "insight", "anxiety_tip")
TYPE_LABELS = {
    "pitch":       "Ecko Pitch",
    "intro":       "自我介紹",
    "insight":     "洞察 / 破冰話題",
    "anxiety_tip": "焦慮應對策略",
}


def _multiline_input(prompt: str, existing: str = "") -> str:
    """讀取多行輸入，Enter 兩次結束。"""
    if existing:
        console.print(f"  [dim]現有內容（直接輸入覆蓋，留空保留）：[/dim]")
        console.print(f"  [dim]{existing[:120]}{'…' if len(existing) > 120 else ''}[/dim]\n")
    console.print(f"  {prompt}（多行請換行，輸入完後按 Enter 兩次）：")
    lines: list[str] = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    result = "\n".join(lines).strip()
    return result if result else existing


def add_entry(type_: str) -> None:
    if type_ not in VALID_TYPES:
        console.print(f"[red]❌  type 必須是：{', '.join(VALID_TYPES)}[/red]")
        sys.exit(1)

    db.init()
    label = TYPE_LABELS[type_]
    console.print(Panel.fit(f"[bold]新增【{label}】[/bold]", border_style="cyan"))

    console.print("  標題（一行摘要）：", end=" ")
    title   = input().strip()
    content = _multiline_input("內容")

    if not title or not content:
        console.print("[red]❌  標題和內容不能為空。[/red]")
        sys.exit(1)

    entry_id = db.add_brain(type_=type_, title=title, content=content)
    console.print(f"\n[green]✅  已新增【{label}】ID {entry_id}：{title}[/green]")
    console.print("   下次執行 prep.py 時自動帶入。\n")


def edit_entry(entry_id: int) -> None:
    db.init()
    entries = db.list_brain()
    target  = next((e for e in entries if e.id == entry_id), None)

    if not target:
        console.print(f"[red]❌  找不到 ID {entry_id}。[/red]")
        sys.exit(1)

    label = TYPE_LABELS.get(target.type, target.type)
    console.print(Panel.fit(f"[bold]編輯【{label}】ID {entry_id}：{target.title}[/bold]", border_style="cyan"))

    console.print(f"  新標題 [dim]（留空保留「{target.title}」）[/dim]：", end=" ")
    new_title   = input().strip() or target.title
    new_content = _multiline_input("新內容", existing=target.content)

    db.update_brain(entry_id=entry_id, title=new_title, content=new_content)
    console.print(f"\n[green]✅  已更新 ID {entry_id}：{new_title}[/green]\n")


def list_entries(type_: str | None = None) -> None:
    db.init()
    entries = db.list_brain(type_)

    if not entries:
        label = f"【{TYPE_LABELS.get(type_, type_)}】" if type_ else "第二大腦"
        console.print(f"📭  {label} 還是空的。執行 python brain.py add <type> 新增。")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("ID",   width=4,  justify="right")
    table.add_column("狀態", width=6)
    table.add_column("類型", width=12)
    table.add_column("標題", width=18)
    table.add_column("內容預覽", min_width=30)

    for e in entries:
        status  = "[green]✅[/green]" if e.active else "[dim]💤[/dim]"
        preview = e.content.replace("\n", " ")[:60]
        if len(e.content) > 60:
            preview += "…"
        table.add_row(
            str(e.id), status,
            TYPE_LABELS.get(e.type, e.type),
            e.title, f"[dim]{preview}[/dim]",
        )

    console.print(Panel(table, title="[bold]第二大腦[/bold]", border_style="cyan"))


def set_active(entry_id: int, active: bool) -> None:
    db.init()
    entries = db.list_brain()
    target  = next((e for e in entries if e.id == entry_id), None)
    if not target:
        console.print(f"[red]❌  找不到 ID {entry_id}。[/red]")
        sys.exit(1)
    db.set_brain_active(entry_id=entry_id, active=active)
    action = "啟用" if active else "封存"
    console.print(f"[green]✅  已{action} [{entry_id}] {target.title}[/green]")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0]
    if cmd == "add":
        t = args[1] if len(args) > 1 else input("類型（pitch/intro/insight/anxiety_tip）：").strip()
        add_entry(t)
    elif cmd == "edit":
        if len(args) < 2:
            console.print("用法：python brain.py edit <id>")
        else:
            edit_entry(int(args[1]))
    elif cmd == "list":
        list_entries(args[1] if len(args) > 1 else None)
    elif cmd == "off":
        set_active(int(args[1]), False)
    elif cmd == "on":
        set_active(int(args[1]), True)
    else:
        console.print(f"[red]❌  未知指令：{cmd}[/red]")
        print(__doc__)


if __name__ == "__main__":
    main()
