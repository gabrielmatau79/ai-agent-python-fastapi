from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.memory.base import ChatMessage


def build_agent_messages(
    *,
    system_prompt: str,
    response_language: str,
    history: list[ChatMessage],
    rag_context: list[str],
    user_input: str,
) -> list[BaseMessage]:
    context_block = (
        "\n\n".join(f"[{idx}] {item}" for idx, item in enumerate(rag_context, start=1))
        or "No relevant RAG context found."
    )
    system_content = (
        f"{system_prompt}\n\n"
        f"Respond in {response_language} unless the user explicitly asks for another language.\n"
        "Use the retrieved context when it is relevant, "
        "but do not claim it says something it does not.\n"
        "If the retrieved context is insufficient, "
        "answer honestly and rely on your general reasoning.\n\n"
        "<retrieved_context>\n"
        f"{context_block}\n"
        "</retrieved_context>"
    )
    messages: list[BaseMessage] = [SystemMessage(content=system_content)]
    for item in history:
        if item.role == "assistant":
            messages.append(AIMessage(content=item.content))
        else:
            messages.append(HumanMessage(content=item.content))
    messages.append(HumanMessage(content=user_input))
    return messages
