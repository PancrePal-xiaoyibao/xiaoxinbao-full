from __future__ import annotations

from xiaoxinbao.modules.llm.base import LLMGateway, LLMMessage


class MockGateway(LLMGateway):
    async def chat(self, messages: list[LLMMessage], model: str | None = None) -> str:
        user_message = next(
            (message["content"] for message in reversed(messages) if message["role"] == "user"),
            "",
        )
        summary = user_message.split("Knowledge Context:", maxsplit=1)[0].strip()
        if "自伤" in user_message or "伤害自己" in user_message:
            return "小馨宝提醒：如果你正处于紧急危险中，请立刻联系当地紧急援助资源和可信任的人。"
        return f"小馨宝回应：我听见你在说“{summary}”。我们先一起把感受说清楚。"
