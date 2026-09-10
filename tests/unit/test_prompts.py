from app.memory.base import ChatMessage
from app.utils.prompts import build_agent_messages


def test_prompt_building_contains_history_and_context() -> None:
    messages = build_agent_messages(
        system_prompt="You are helpful.",
        response_language="en",
        history=[ChatMessage(role="user", content="Hello")],
        rag_context=["Kubernetes manages containers."],
        user_input="What is Kubernetes?",
    )
    assert len(messages) == 3
    assert "Kubernetes manages containers" in str(messages[0].content)
    assert str(messages[1].content) == "Hello"
