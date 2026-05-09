"""AI API 客户端抽象接口"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AIMessage:
    role: str
    content: str


class AIClient(ABC):
    """AI 客户端抽象基类"""

    @abstractmethod
    def chat(self, messages: list[AIMessage], **kwargs) -> str:
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        ...


class ClaudeClient(AIClient):
    """Claude API 客户端"""

    def __init__(self, api_key: str = "", model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list[AIMessage], **kwargs) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)

        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_msg += msg.content + "\n"
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})

        response = client.messages.create(
            model=self.model,
            system=system_msg.strip() or None,
            messages=chat_messages,
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        return response.content[0].text

    def count_tokens(self, text: str) -> int:
        """粗略估计中英文混合文本的 token 数"""
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        other_chars = len(text) - chinese_chars
        return chinese_chars // 2 + other_chars // 4


class OpenAIClient(AIClient):
    """OpenAI 兼容接口客户端"""

    def __init__(self, api_key: str = "", model: str = "gpt-4o", base_url: str = ""):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def chat(self, messages: list[AIMessage], **kwargs) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url or None)

        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        response = client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        return response.choices[0].message.content

    def count_tokens(self, text: str) -> int:
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        other_chars = len(text) - chinese_chars
        return chinese_chars // 2 + other_chars // 4


def create_ai_client(api_type: str = "claude", api_key: str = "", model: str = "") -> AIClient:
    """AI 客户端工厂函数"""
    if api_type == "openai":
        return OpenAIClient(api_key=api_key, model=model or "gpt-4o")
    return ClaudeClient(api_key=api_key, model=model or "claude-sonnet-4-20250514")
