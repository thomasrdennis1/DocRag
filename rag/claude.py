"""
Anthropic Claude API: streaming responses with source context.
"""

import os
import json

import anthropic

from .config import MODEL_NAME


_SYSTEM_PROMPT = """You are a knowledgeable research assistant with access to a large document library. The user has asked a question and you have been given the most relevant passages from the document database.

Guidelines:
- Cite sources inline: (Source N — Filename, Page X)
- If multiple documents agree or differ, note it.
- Be thorough and specific — the user needs actionable information.
- If the passages don't fully answer the question, say so and explain what's missing.
- Structure your answer clearly with paragraphs. Use markdown formatting where helpful.
- Never fabricate information not present in the sources."""


def _build_context(question: str, chunks: list[dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_label = f"{chunk.get('directory', '')}/{chunk['filename']}" if chunk.get('directory') else chunk['filename']
        context_parts.append(
            f"[Source {i}: {source_label}, Page {chunk['page']}]\n"
            f"{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)
    return f"Question: {question}\n\nRelevant passages from the document database:\n\n{context}\n\nPlease answer the question based on these passages."


def ask_claude(question: str, chunks: list[dict]):
    """SSE generator for Flask (legacy)."""
    from .config import get as cfg_get
    api_key = os.environ.get("ANTHROPIC_API_KEY", "") or cfg_get("anthropic_api_key") or ""
    if not api_key:
        yield "data: " + json.dumps({"error": "ANTHROPIC_API_KEY not set. Add it to your environment and restart."}) + "\n\n"
        return

    client = anthropic.Anthropic(api_key=api_key)
    user_message = _build_context(question, chunks)

    try:
        with client.messages.stream(
            model=MODEL_NAME,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        ) as stream_obj:
            for text in stream_obj.text_stream:
                yield "data: " + json.dumps({"delta": text}) + "\n\n"
        yield "data: " + json.dumps({"done": True}) + "\n\n"
    except anthropic.AuthenticationError:
        yield "data: " + json.dumps({"error": "Invalid API key. Check ANTHROPIC_API_KEY."}) + "\n\n"
    except Exception as e:
        yield "data: " + json.dumps({"error": str(e)}) + "\n\n"


def stream_claude(question: str, chunks: list[dict]):
    """Plain-text generator for Streamlit st.write_stream()."""
    from .config import get as cfg_get
    api_key = os.environ.get("ANTHROPIC_API_KEY", "") or cfg_get("anthropic_api_key") or ""
    if not api_key:
        yield "⚠️ **ANTHROPIC_API_KEY not set.** Add it to your `.env` file and restart."
        return

    client = anthropic.Anthropic(api_key=api_key)
    user_message = _build_context(question, chunks)

    try:
        with client.messages.stream(
            model=MODEL_NAME,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        ) as stream_obj:
            for text in stream_obj.text_stream:
                yield text
    except anthropic.AuthenticationError:
        yield "⚠️ **Invalid API key.** Check your `ANTHROPIC_API_KEY`."
    except Exception as e:
        yield f"⚠️ **Error:** {e}"
