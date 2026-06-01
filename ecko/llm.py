"""
llm.py — Claude API wrapper

PrepGenerator 類別：讀取 brain DB 內容，組裝 system / user prompt，
呼叫 Claude API，回傳可直接寫入 Markdown 的字串。
"""

import anthropic
from ecko.models import Event, BrainEntry, UserConfig

# ── Prompt 模板 ───────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 {name} 的社交準備助理。

關於 {name}：
- 她是 {product} 的創辦人：{tagline}
- 她有社交焦慮，偏好深度的一對一對話，不擅長同時應對多人
- 她不喜歡推銷感，話題要像真誠的好奇，不是 pitch
- 她需要可以直接說出口的完整句子，不是「可以聊 X 主題」這種模糊建議

她的核心素材（第二大腦）：
{brain_block}

生成規則：
1. 破冰話題必須是一句可以直接說出口的完整句子
2. 自我介紹不超過 75 字，結尾留一個讓對方想接話的鉤子
3. 直接輸出 Markdown，不要說「我來幫你...」或「以下是...」
4. 語氣真誠、不誇張、不過度包裝
"""

USER_PROMPT_MEETUP = """\
活動名稱：{name}
活動類型：小型聚會（{notes}）
地點：{location}

請生成以下四個區塊（Markdown 格式，直接輸出，不要前言）：

## 🗣️ 30 秒自我介紹
（針對這場小型聚會的語氣調整，自然、不像在台上講話）

## 💡 破冰話題
（3 個，每個是一句完整可直接說出口的話，附一行「為什麼這句話適合這場活動」）

## 🎯 今天的最小行動目標
（一件具體的事，做到就算成功，不要寫「盡力而為」這種廢話）

## 🚨 退場台詞
（一句在任何時機都能自然使用的離場說法）
"""

USER_PROMPT_COFFEE = """\
Coffee Chat 對象：{name}
對方背景：{notes}
地點：{location}

請生成以下四個區塊（Markdown 格式，直接輸出）：

## 🗣️ 開場白
（第一句話，讓對方感受到你是真的對他有興趣，不是在走流程）

## 💡 想聊的問題
（3 個問題，每個問題後面附「為什麼問這個」）

## 🎯 這次 coffee chat 的目標
（一個具體的收穫，不是「建立關係」這種虛的）

## 🚨 如果話題卡住了
（一句可以重新啟動對話的話）
"""


# ── PrepGenerator ──────────────────────────────────────────────────────────────

class PrepGenerator:
    def __init__(self, config: UserConfig):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)

    def _build_brain_block(self, brain_entries: dict[str, list[BrainEntry]]) -> str:
        lines = []
        type_labels = {
            "pitch":       "Product Pitch",
            "intro":       "自我介紹素材",
            "insight":     "個人洞察 / 話題素材",
            "anxiety_tip": "焦慮應對策略",
        }
        for type_, entries in brain_entries.items():
            if not entries:
                continue
            label = type_labels.get(type_, type_)
            lines.append(f"[{label}]")
            for e in entries:
                lines.append(f"  • {e.title}: {e.content}")
        return "\n".join(lines) if lines else "（尚未設定第二大腦內容）"

    def _build_system(self, brain_entries: dict[str, list[BrainEntry]]) -> str:
        return SYSTEM_PROMPT.format(
            name=self.config.name,
            product=self.config.product,
            tagline=self.config.tagline,
            brain_block=self._build_brain_block(brain_entries),
        )

    def _build_user(self, event: Event) -> str:
        template = USER_PROMPT_COFFEE if event.type == "coffee_chat" else USER_PROMPT_MEETUP
        return template.format(
            name=event.name,
            notes=event.notes or "小型技術聚會",
            location=event.location or "（未填）",
        )

    def generate(self, event: Event, brain_entries: dict[str, list[BrainEntry]]) -> str:
        """呼叫 Claude API，回傳生成的 Markdown 字串。"""
        system = self._build_system(brain_entries)
        user   = self._build_user(event)

        message = self.client.messages.create(
            model=self.config.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text
