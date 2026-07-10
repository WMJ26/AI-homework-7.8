from abc import ABC, abstractmethod
import os


class LLMProvider(ABC):
    @abstractmethod
    def invoke(self, messages: list[dict]) -> str:
        ...

    @abstractmethod
    async def ainvoke(self, messages: list[dict]) -> str:
        ...


class MockLLM(LLMProvider):
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self._index = 0

    def invoke(self, messages: list[dict]) -> str:
        if self._index >= len(self._responses):
            raise IndexError("No more mock responses available")
        response = self._responses[self._index]
        self._index += 1
        return response

    async def ainvoke(self, messages: list[dict]) -> str:
        return self.invoke(messages)


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. Set it via environment variable "
                "or pass it directly to OpenAIProvider(api_key=...)"
            )
        self.model = model

    def invoke(self, messages: list[dict]) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content

    async def ainvoke(self, messages: list[dict]) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. Set it via environment variable "
                "or pass it directly to AnthropicProvider(api_key=...)"
            )
        self.model = model

    def invoke(self, messages: list[dict]) -> str:
        from anthropic import Anthropic
        client = Anthropic(api_key=self.api_key)
        system = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                user_messages.append(msg)
        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system if system else None,
            messages=user_messages,
        )
        return response.content[0].text

    async def ainvoke(self, messages: list[dict]) -> str:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=self.api_key)
        system = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                user_messages.append(msg)
        response = await client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system if system else None,
            messages=user_messages,
        )
        return response.content[0].text