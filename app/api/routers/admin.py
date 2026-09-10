from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.api.deps import get_config_service, get_settings, verify_api_key_for_page
from app.core.exceptions import ApplicationError
from app.core.settings import Settings
from app.core.templates import templates
from app.schemas.config import to_editable_sections

router = APIRouter(prefix="/admin", tags=["admin"])

SECTIONS = ("llm", "agent", "memory", "rag", "tools", "mcp")


@router.get("/", response_class=HTMLResponse)
async def admin_index(
    request: Request,
    _: None = Depends(verify_api_key_for_page),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "admin/index.html",
        {
            "sections": to_editable_sections(settings),
            "api_key": request.query_params.get("key", ""),
        },
    )


def _bool_from_form(form: Any, name: str) -> bool:
    values = form.getlist(name)
    if not values:
        return False
    return bool(values[-1] == "true")


def _optional(value: str | None) -> str | None:
    return value if value else None


def _patch_from_form(section: str, form: Any) -> dict[str, Any]:
    if section == "llm":
        return {
            "llm_provider": form.get("llmProvider"),
            "llm_model": form.get("llmModel"),
            "llm_temperature": float(form.get("llmTemperature")),
            "llm_max_tokens": int(form.get("llmMaxTokens")),
            "llm_timeout_seconds": float(form.get("llmTimeoutSeconds")),
            "openai_api_key": _optional(form.get("openaiApiKey")),
            "openai_model": form.get("openaiModel"),
            "ollama_base_url": form.get("ollamaBaseUrl"),
            "ollama_model": form.get("ollamaModel"),
            "anthropic_api_key": _optional(form.get("anthropicApiKey")),
            "anthropic_model": form.get("anthropicModel"),
        }
    if section == "agent":
        return {
            "agent_prompt": form.get("agentPrompt"),
            "default_response_language": form.get("defaultResponseLanguage"),
            "language_detection_enabled": _bool_from_form(form, "languageDetectionEnabled"),
        }
    if section == "memory":
        return {
            "agent_memory_type": form.get("agentMemoryType"),
            "agent_memory_window": int(form.get("agentMemoryWindow")),
            "memory_ttl_seconds": int(form.get("memoryTtlSeconds")),
            "redis_url": form.get("redisUrl"),
        }
    if section == "rag":
        return {
            "rag_provider": form.get("ragProvider"),
            "rag_docs_path": form.get("ragDocsPath"),
            "rag_top_k": int(form.get("ragTopK")),
            "rag_chunk_size": int(form.get("ragChunkSize")),
            "rag_chunk_overlap": int(form.get("ragChunkOverlap")),
            "embedding_provider": form.get("embeddingProvider"),
            "embedding_model": form.get("embeddingModel"),
            "vector_store": form.get("vectorStore"),
            "vector_index_name": form.get("vectorIndexName"),
        }
    if section == "tools":
        return {
            "llm_tools_config": form.get("llmToolsConfig"),
            "llm_tools_auth_token": _optional(form.get("llmToolsAuthToken")),
            "llm_tools_auth_header": form.get("llmToolsAuthHeader"),
            "llm_tools_auth_scheme": form.get("llmToolsAuthScheme"),
        }
    return {
        "mcp_servers": form.get("mcpServers"),
        "mcp_tool_timeout_ms": int(form.get("mcpToolTimeoutMs")),
        "mcp_throw_on_load_error": _bool_from_form(form, "mcpThrowOnLoadError"),
        "mcp_use_standard_content_blocks": _bool_from_form(form, "mcpUseStandardContentBlocks"),
        "mcp_auth_token": _optional(form.get("mcpAuthToken")),
        "mcp_auth_header": form.get("mcpAuthHeader"),
    }


@router.post("/config/{section}", response_class=HTMLResponse)
async def save_section(
    section: str,
    request: Request,
    _: None = Depends(verify_api_key_for_page),
    config_service: Any = Depends(get_config_service),
) -> HTMLResponse:
    if section not in SECTIONS:
        return templates.TemplateResponse(
            request,
            "admin/_feedback.html",
            {"ok": False, "message": f"Unknown section: {section}"},
        )
    form = await request.form()
    try:
        patch = _patch_from_form(section, form)
        result = await config_service.apply_patch(patch)
    except ApplicationError as exc:
        return templates.TemplateResponse(
            request, "admin/_feedback.html", {"ok": False, "message": str(exc)}
        )
    except (ValueError, TypeError) as exc:
        return templates.TemplateResponse(
            request, "admin/_feedback.html", {"ok": False, "message": f"Invalid input: {exc}"}
        )
    return templates.TemplateResponse(
        request,
        "admin/_feedback.html",
        {"ok": True, "rebuilt": result.rebuilt, "warnings": result.warnings},
    )
