"""
llm.py — OpenAI-compatible API wrapper

PrepGenerator 類別：讀取 brain DB 內容，組裝 system / user prompt，
呼叫 OpenAI-compatible API（支援 Anthropic、Aliyun DashScope、OpenRouter 等），
回傳可直接寫入 Markdown 的字串。
"""

from openai import OpenAI
from ecko.models import Event, BrainEntry, Contact, UserConfig

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

FOLLOWUP_SYSTEM_PROMPT = """\
你是 {name} 的 follow-up 訊息助理。

關於 {name}：
- 她是 {product} 的創辦人：{tagline}
- 她的溝通風格：真誠、不推銷感、每句話都有具體的資訊量

她的核心素材：
{brain_block}

訊息必須包含以下三層，順序不變：
1. 【連結層】第一句提到對話裡的一個具體細節，讓對方知道你真的記得——不是「很高興認識你」
2. 【價值層】你在對話後想到的 insight、資源或提案——給對方帶來東西，不是索取；這層要用「我後來想到⋯」或「我想分享⋯」這樣的語氣帶出
3. 【行動層】一個具體的下一步提議，說清楚形式（例如「我可以傳你 beta 連結試用」「你方便的話我們約 20 分鐘 call？」）——不是「有空喝咖啡」

格式規則：
- LinkedIn：整則不超過 80 字，三層合為一段自然的訊息
- Email：第一行「主旨：xxx」，內文三層可各一句，不超過 150 字
- 直接輸出訊息本文，不加任何說明或前言
"""

FOLLOWUP_USER_PROMPT = """\
對象：{name}
對方背景：{role}
我們聊的話題：{notes}
這次 follow-up 想帶給對方的東西：{intent}
傳送平台：{platform}

請依照三層結構（連結→價值→行動）生成一則可直接傳送的訊息。
"""


# ── PrepGenerator ──────────────────────────────────────────────────────────────

class PrepGenerator:
    def __init__(self, config: UserConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )

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
        """呼叫 OpenAI-compatible API，回傳生成的 Markdown 字串。"""
        system = self._build_system(brain_entries)
        user   = self._build_user(event)

        kwargs = dict(
            model=self.config.model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )
        # Aliyun Qwen 需要明確關閉 thinking mode，其他 supplier 不支援此參數
        if "aliyuncs.com" in self.config.base_url:
            kwargs["extra_body"] = {"enable_thinking": False}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def generate_followup(
        self,
        contact: Contact,
        brain_entries: dict[str, list[BrainEntry]],
        platform: str = "LinkedIn",
        intent: str = "",
    ) -> str:
        """根據聯絡人備註生成 follow-up 訊息草稿。"""
        system = FOLLOWUP_SYSTEM_PROMPT.format(
            name=self.config.name,
            product=self.config.product,
            tagline=self.config.tagline,
            brain_block=self._build_brain_block(brain_entries),
        )
        user = FOLLOWUP_USER_PROMPT.format(
            name=contact.name,
            role=contact.role or "（未填）",
            notes=contact.notes or "（未記錄）",
            intent=intent or "分享一個和對話主題相關的觀察或資源",
            platform=platform,
        )

        kwargs = dict(
            model=self.config.model,
            max_tokens=512,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )
        if "aliyuncs.com" in self.config.base_url:
            kwargs["extra_body"] = {"enable_thinking": False}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
