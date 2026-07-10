import pytest
from fixlot.core.llm import LLMProvider, MockLLM, OpenAIProvider, AnthropicProvider


class TestMockLLM:
    def test_returns_preset_responses_in_order(self):
        llm = MockLLM(["hello", "world"])
        assert llm.invoke([{"role": "user", "content": "test"}]) == "hello"
        assert llm.invoke([{"role": "user", "content": "test"}]) == "world"

    def test_raises_when_no_more_responses(self):
        llm = MockLLM(["only one"])
        llm.invoke([{"role": "user", "content": "test"}])
        with pytest.raises(IndexError, match="No more mock responses"):
            llm.invoke([{"role": "user", "content": "test"}])

    def test_async_invoke_returns_preset_responses(self):
        import asyncio
        llm = MockLLM(["async hello"])
        result = asyncio.run(llm.ainvoke([{"role": "user", "content": "test"}]))
        assert result == "async hello"

    def test_mock_llm_is_instance_of_llm_provider(self):
        llm = MockLLM([])
        assert isinstance(llm, LLMProvider)


class TestLLMProvider:
    def test_abstract_class_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            LLMProvider()

    def test_abstract_class_defines_interface(self):
        assert hasattr(LLMProvider, "invoke")
        assert hasattr(LLMProvider, "ainvoke")


class TestOpenAIProvider:
    def test_requires_api_key(self):
        import os
        old_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                OpenAIProvider()
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key

    def test_accepts_api_key_directly(self):
        provider = OpenAIProvider(api_key="sk-test")
        assert provider.api_key == "sk-test"

    def test_has_model_parameter(self):
        provider = OpenAIProvider(api_key="sk-test", model="gpt-4o")
        assert provider.model == "gpt-4o"


class TestAnthropicProvider:
    def test_requires_api_key(self):
        import os
        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                AnthropicProvider()
        finally:
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key

    def test_accepts_api_key_directly(self):
        provider = AnthropicProvider(api_key="sk-ant-test")
        assert provider.api_key == "sk-ant-test"

    def test_has_model_parameter(self):
        provider = AnthropicProvider(api_key="sk-ant-test", model="claude-sonnet-4-20250514")
        assert provider.model == "claude-sonnet-4-20250514"