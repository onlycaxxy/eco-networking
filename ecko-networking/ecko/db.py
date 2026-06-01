"""
db.py — 資料庫層

使用 context manager 管理連線，確保每次操作都正確 commit / rollback。
所有腳本透過 NetworkingDB 存取資料，不直接操作 sqlite3。
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from ecko.models import Event, Contact, Takeaway, BrainEntry

DB_PATH  = Path(__file__).parent.parent / "events.db"
PREP_DIR = Path(__file__).parent.parent / "prep"


class NetworkingDB:
    def __init__(self, path: Path = DB_PATH):
        self.path = path
        PREP_DIR.mkdir(parents=True, exist_ok=True)

    # ── 連線管理 ──────────────────────────────────────────────────────────────

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ── 初始化 ────────────────────────────────────────────────────────────────

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL,
                    datetime    TEXT    NOT NULL,
                    type        TEXT    DEFAULT 'meetup',
                    location    TEXT    DEFAULT '',
                    url         TEXT    DEFAULT '',
                    notes       TEXT    DEFAULT '',
                    created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS contacts (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id        INTEGER REFERENCES events(id),
                    name            TEXT    NOT NULL,
                    role            TEXT    DEFAULT '',
                    contact         TEXT    DEFAULT '',
                    notes           TEXT    DEFAULT '',
                    follow_up_by    TEXT,
                    follow_up_done  INTEGER DEFAULT 0,
                    created_at      TEXT    DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS takeaways (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id    INTEGER REFERENCES events(id),
                    content     TEXT    NOT NULL,
                    created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS brain (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    type        TEXT    NOT NULL,
                    title       TEXT    NOT NULL,
                    content     TEXT    NOT NULL,
                    active      INTEGER DEFAULT 1,
                    created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
                );
            """)

    # ── Events ────────────────────────────────────────────────────────────────

    def add_event(self, name: str, datetime: str, type_: str = "meetup",
                  location: str = "", url: str = "", notes: str = "") -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO events (name, datetime, type, location, url, notes) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (name, datetime, type_, location, url, notes),
            )
            return cur.lastrowid

    def get_event(self, event_id: int) -> Optional[Event]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM events WHERE id = ?", (event_id,)
            ).fetchone()
        if not row:
            return None
        return Event(**dict(row))

    def list_events(self, upcoming_only: bool = True) -> list[Event]:
        with self.connect() as conn:
            if upcoming_only:
                from datetime import datetime
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                rows = conn.execute(
                    "SELECT * FROM events WHERE datetime >= ? ORDER BY datetime ASC", (now,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM events ORDER BY datetime ASC"
                ).fetchall()
        return [Event(**dict(r)) for r in rows]

    # ── Contacts ──────────────────────────────────────────────────────────────

    def add_contact(self, event_id: int, name: str, role: str = "",
                    contact: str = "", notes: str = "",
                    follow_up_by: Optional[str] = None) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO contacts (event_id, name, role, contact, notes, follow_up_by) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (event_id, name, role, contact, notes, follow_up_by),
            )
            return cur.lastrowid

    def list_contacts(self, event_id: Optional[int] = None) -> list[Contact]:
        with self.connect() as conn:
            if event_id:
                rows = conn.execute(
                    "SELECT * FROM contacts WHERE event_id = ? ORDER BY id ASC", (event_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM contacts ORDER BY id DESC"
                ).fetchall()
        return [Contact(
            id=r["id"], event_id=r["event_id"], name=r["name"],
            role=r["role"], contact=r["contact"], notes=r["notes"],
            follow_up_by=r["follow_up_by"],
            follow_up_done=bool(r["follow_up_done"]),
            created_at=r["created_at"],
        ) for r in rows]

    def pending_followups(self) -> list[Contact]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM contacts WHERE follow_up_by IS NOT NULL "
                "AND follow_up_done = 0 ORDER BY follow_up_by ASC"
            ).fetchall()
        return [Contact(
            id=r["id"], event_id=r["event_id"], name=r["name"],
            role=r["role"], contact=r["contact"], notes=r["notes"],
            follow_up_by=r["follow_up_by"],
            follow_up_done=bool(r["follow_up_done"]),
            created_at=r["created_at"],
        ) for r in rows]

    def mark_followup_done(self, contact_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE contacts SET follow_up_done = 1 WHERE id = ?", (contact_id,)
            )

    # ── Takeaways ─────────────────────────────────────────────────────────────

    def add_takeaway(self, event_id: int, content: str) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO takeaways (event_id, content) VALUES (?, ?)",
                (event_id, content),
            )
            return cur.lastrowid

    def list_takeaways(self, event_id: int) -> list[Takeaway]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM takeaways WHERE event_id = ? ORDER BY id ASC", (event_id,)
            ).fetchall()
        return [Takeaway(**dict(r)) for r in rows]

    # ── Brain ─────────────────────────────────────────────────────────────────

    def add_brain(self, type_: str, title: str, content: str) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO brain (type, title, content) VALUES (?, ?, ?)",
                (type_, title, content),
            )
            return cur.lastrowid

    def get_brain(self, type_: str) -> list[BrainEntry]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM brain WHERE type = ? AND active = 1 ORDER BY id DESC", (type_,)
            ).fetchall()
        return [BrainEntry(
            id=r["id"], type=r["type"], title=r["title"],
            content=r["content"], active=bool(r["active"]), created_at=r["created_at"],
        ) for r in rows]

    def list_brain(self, type_: Optional[str] = None) -> list[BrainEntry]:
        with self.connect() as conn:
            if type_:
                rows = conn.execute(
                    "SELECT * FROM brain WHERE type = ? ORDER BY active DESC, id DESC", (type_,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM brain ORDER BY type, active DESC, id DESC"
                ).fetchall()
        return [BrainEntry(
            id=r["id"], type=r["type"], title=r["title"],
            content=r["content"], active=bool(r["active"]), created_at=r["created_at"],
        ) for r in rows]

    def update_brain(self, entry_id: int, title: str, content: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE brain SET title = ?, content = ? WHERE id = ?",
                (title, content, entry_id),
            )

    def set_brain_active(self, entry_id: int, active: bool) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE brain SET active = ? WHERE id = ?", (int(active), entry_id)
            )
