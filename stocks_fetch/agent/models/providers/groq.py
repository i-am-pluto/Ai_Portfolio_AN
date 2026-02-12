"""Groq model gateway."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from stocks_fetch.agent.config import AgentConfig
from stocks_fetch.agent.models.base import ModelGateway


class GroqModelGateway(ModelGateway):
    """Groq-backed gateway implementation."""

    def __init__(self, config: AgentConfig) -> None:
        self._model = ChatGroq(
            api_key=config.groq_api_key,
            model=config.groq_model,
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
