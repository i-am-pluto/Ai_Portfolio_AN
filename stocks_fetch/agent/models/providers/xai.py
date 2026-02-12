"""xAI/Grok model gateway."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from stocks_fetch.agent.config import AgentConfig
from stocks_fetch.agent.models.base import ModelGateway


class XaiModelGateway(ModelGateway):
    """xAI-backed gateway implementation."""

    def __init__(self, config: AgentConfig) -> None:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise RuntimeError(
                "LLM_PROVIDER is set to grok/xai, but langchain-openai is not installed. "
                "Install dependencies with `uv sync`."
            ) from exc

        self._model = ChatOpenAI(
            api_key=config.grok_api_key,
            model=config.grok_model,
            base_url=config.xai_base_url,
            temperature=0.15,
        )

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        response = self._model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        return response.content if isinstance(response.content, str) else str(response.content)
