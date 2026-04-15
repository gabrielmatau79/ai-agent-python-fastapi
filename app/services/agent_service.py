from __future__ import annotations

from app.core.settings import Settings
from app.schemas.agent import AgentAskRequest
from app.services.llm_service import LlmService
from app.services.memory_service import MemoryService
from app.services.rag_service import RagService
from app.utils.language import detect_language
from app.utils.prompts import build_agent_messages


class AgentService:
    def __init__(
        self,
        settings: Settings,
        rag_service: RagService,
        llm_service: LlmService,
        memory_service: MemoryService,
    ) -> None:
        self._settings = settings
        self._rag_service = rag_service
        self._llm_service = llm_service
        self._memory_service = memory_service

    async def ask(self, payload: AgentAskRequest) -> str:
        language = payload.user_lang
        if not language and self._settings.language_detection_enabled:
            language = detect_language(
                payload.user_input, default=self._settings.default_response_language
            )
        language = language or self._settings.default_response_language

        history = await self._memory_service.get_history(payload.session_id)
        rag_results = await self._rag_service.retrieve(
            payload.user_input, top_k=self._settings.rag_top_k
        )
        messages = build_agent_messages(
            system_prompt=self._settings.agent_prompt,
            response_language=language,
            history=history,
            rag_context=[result.content for result in rag_results],
            user_input=payload.user_input,
        )
        answer = await self._llm_service.generate(messages, session_id=payload.session_id)
        await self._memory_service.add_message(payload.session_id, "user", payload.user_input)
        await self._memory_service.add_message(payload.session_id, "assistant", answer)
        return answer
