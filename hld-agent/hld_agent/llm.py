"""Thin LLM seam: every node asks for a validated Pydantic object, nothing else.

`ctx` carries the same facts as the prompt in structured form. Real models ignore it; the
scripted test double (hld_agent.testing.fake_llm) uses it so the graph can be exercised offline.
"""
from __future__ import annotations

import logging
from typing import Protocol, TypeVar

from pydantic import BaseModel

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLM(Protocol):
    def structured(self, schema: type[T], system: str, user: str, *, task: str, ctx: dict | None = None) -> T: ...


class LangChainLLM:
    """Any LangChain chat model via init_chat_model, e.g. 'google_vertexai:gemini-2.5-pro',
    'google_genai:gemini-2.5-flash', 'anthropic:claude-sonnet-4-5'. Per-task overrides let you run
    the critic on a different (or cheaper) model than the author — a second model family as
    reviewer catches more of the author's blind spots."""

    def __init__(self, model: str, temperature: float = 0.2, task_models: dict[str, str] | None = None,
                 max_retries: int = 2, **kwargs):
        from langchain.chat_models import init_chat_model
        self._init = lambda m: init_chat_model(m, temperature=temperature, **kwargs)
        self._default = self._init(model)
        self._by_task = {t: self._init(m) for t, m in (task_models or {}).items()}
        self._retries = max_retries

    def structured(self, schema, system, user, *, task, ctx=None):
        model = self._by_task.get(task, self._default)
        runnable = model.with_structured_output(schema).with_retry(stop_after_attempt=self._retries + 1)
        result = runnable.invoke([("system", system), ("human", user)])
        if isinstance(result, dict):          # some providers return dicts
            result = schema.model_validate(result)
        return result


def build_llm(cfg: dict) -> LLM:
    model = cfg.get("model", "")
    if model in ("fake", "scripted"):
        from .testing.fake_llm import ScriptedLLM
        log.warning("Using the scripted test LLM: output shows structure only, not real design quality.")
        return ScriptedLLM()
    if not model:
        raise ValueError("llm.model is required (e.g. google_vertexai:gemini-2.5-pro)")
    return LangChainLLM(model, temperature=cfg.get("temperature", 0.2),
                        task_models=cfg.get("task_models"), max_retries=cfg.get("max_retries", 2),
                        **cfg.get("kwargs", {}))
