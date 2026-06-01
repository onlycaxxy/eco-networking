# Ecko Networking System
### A personal CRM for the socially anxious founder

---

## Problem Statement

Most networking tools are built for extroverts.

They assume you enjoy walking into a room full of strangers, that you can context-switch between five conversations at once, and that a "follow-up" is just a quick LinkedIn message away.

For founders with social anxiety, the reality is different. The mental cost of preparing for a single networking event can be high enough to skip it entirely. And when you do attend, the cognitive load of remembering what to say, who you met, and what to do next often means the opportunity disappears within 48 hours.

This system is built for one specific person: a founder who knows that real connections matter, hates the performative side of networking, and needs a structured external brain to make the whole process less exhausting.

---

## Design Philosophy

**1. Reduce activation energy, not just effort.**
The hardest part of networking isn't the event itself — it's starting. Every script in this system is designed to be run in under 2 minutes, with no decisions to make on the spot.

**2. Personalization over templates.**
A generic icebreaker ("What do you do?") is useless. This system uses your own second brain — your pitch, your insights, your anxiety strategies — as input to a Claude API call that generates content specific to you and the event.

**3. The event doesn't end when you leave.**
The most common failure mode in networking is not the event itself but the 48 hours after. The follow-up system exists because connections decay fast, and a good conversation with no follow-up is a missed opportunity.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Entry Points                         │
│  add_event  ·  prep  ·  brain  ·  checkin  ·  followup  ·  list │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
  │  ecko/db.py │   │ ecko/llm.py │   │ecko/models.py│
  │             │   │             │   │             │
  │ NetworkingDB│   │PrepGenerator│   │ dataclasses │
  │ context mgr │   │ Claude API  │   │ type hints  │
  └──────┬──────┘   └──────┬──────┘   └─────────────┘
         │                 │
         ▼                 ▼
  ┌─────────────┐   ┌─────────────┐
  │  events.db  │   │ Anthropic   │
  │  (SQLite)   │   │  claude-    │
  │             │   │  haiku      │
  └─────────────┘   └─────────────┘
```

---

## Data Model

```
events
  id · name · datetime · type(meetup|coffee_chat)
  location · url · notes

contacts
  id · event_id(FK) · name · role · contact
  notes · follow_up_by · follow_up_done

takeaways
  id · event_id(FK) · content

brain
  id · type(pitch|intro|insight|anxiety_tip)
  title · content · active
```

`brain` is the core differentiator: it's a personal knowledge store that feeds every Claude API call, ensuring generated content reflects your actual voice, product, and communication style — not a generic template.

---

## Key Features

### AI-powered prep generation (`prep.py`)
Calls Claude API with a two-part prompt:
- **System prompt**: your identity, product, and second brain entries
- **User prompt**: event-specific context (type, location, notes)

Generates: personalized 30-sec intro, 3 icebreakers with rationale, minimum action goal, exit line.

Two modes — `meetup` and `coffee_chat` — produce structurally different prompts because the social dynamics are fundamentally different.

### Second brain (`brain.py`)
Four entry types that get injected into every prep:
- `pitch` — your product story, in your words
- `intro` — self-introduction variants
- `insight` — conversation starters tied to your actual thinking
- `anxiety_tip` — strategies you've found actually work for you

Supports add, edit, archive, and restore — because your pitch changes.

### Follow-up system (`checkin.py` + `followup.py`)
After each event: log contacts with optional follow-up deadlines.
`followup.py` surfaces overdue, due-today, and upcoming follow-ups with color-coded terminal output via `rich`.

---

## Installation

```bash
git clone <repo>
cd ecko-networking
pip install -r requirements.txt
python setup.py
```

Then seed your second brain:
```bash
python brain.py add pitch
python brain.py add intro
python brain.py add insight
```

---

## Workflow

```
Before the event
  python add_event.py        # log the event
  python prep.py <id>        # generate AI prep pack → prep/*.md

At the event
  Open the Markdown file in VS Code or any reader

After the event (within 24h)
  python checkin.py <id>     # log contacts + takeaways

Ongoing
  python followup.py         # see who needs a message
  python followup.py done <contact_id>
```

---

## Command Reference

| Script | Command | What it does |
|---|---|---|
| `setup.py` | `python setup.py` | First-time config |
| `add_event.py` | `python add_event.py` | Add meetup or coffee chat |
| `prep.py` | `python prep.py <id>` | Generate AI prep pack |
| `brain.py` | `python brain.py add <type>` | Add brain entry |
| `brain.py` | `python brain.py edit <id>` | Edit existing entry |
| `brain.py` | `python brain.py list` | View all entries |
| `checkin.py` | `python checkin.py <id>` | Post-event logging |
| `followup.py` | `python followup.py` | See pending follow-ups |
| `followup.py` | `python followup.py done <id>` | Mark as done |
| `list.py` | `python list.py` | View events |
| `list.py` | `python list.py contacts` | View all contacts |

---

## Technical Stack

- **Python 3.11+** — `dataclasses`, `contextlib`, `zoneinfo`, type hints throughout
- **SQLite** — local-first, no server, no sync issues
- **Anthropic SDK** — `claude-haiku-4-5-20251001` for cost-efficient generation
- **rich** — terminal UI (tables, panels, color-coded follow-up states)
- **PyYAML** — config management

---

## Roadmap

- [ ] Export contacts to CSV for batch LinkedIn outreach
- [ ] Weekly digest: events attended, contacts made, follow-up completion rate
- [ ] Multiple brain profiles (adjust pitch for different audiences)
- [ ] Web UI with Flask for non-terminal access

---

*Built for Ecko — because even the most anxious thinkers deserve to be heard.*
