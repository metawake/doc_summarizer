import logging

import tiktoken
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# keep chunk size well under model context to leave room for prompt + response
CHUNK_TOKEN_LIMIT = 12_000
MODEL_NAME = settings.openai_model


def count_tokens(text: str, model: str = MODEL_NAME) -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def chunk_text(text: str, max_tokens: int = CHUNK_TOKEN_LIMIT) -> list[str]:
    """Split text into chunks that fit within the token limit.

    Tries to split on paragraph boundaries for cleaner chunks.
    """
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        # single paragraph exceeds limit - split it by lines
        if para_tokens > max_tokens:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0
            lines = para.split("\n")
            line_chunk: list[str] = []
            line_tokens = 0
            for line in lines:
                lt = count_tokens(line)
                if line_tokens + lt > max_tokens and line_chunk:
                    chunks.append("\n".join(line_chunk))
                    line_chunk = []
                    line_tokens = 0
                line_chunk.append(line)
                line_tokens += lt
            if line_chunk:
                chunks.append("\n".join(line_chunk))
            continue

        if current_tokens + para_tokens > max_tokens and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []
            current_tokens = 0

        current_chunk.append(para)
        current_tokens += para_tokens

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


class OpenAISummarizer:
    """Summarizes text using OpenAI with map-reduce for long documents."""

    def __init__(self, api_key: str | None = None, model: str = MODEL_NAME) -> None:
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = model

    def _call_llm(self, prompt: str, text: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
        )
        return response.choices[0].message.content or ""

    def summarize(self, text: str) -> str:
        tokens = count_tokens(text)
        logger.info("Summarizing %d tokens of text", tokens)

        if tokens <= CHUNK_TOKEN_LIMIT:
            return self._summarize_single(text)

        return self._summarize_map_reduce(text)

    def _summarize_single(self, text: str) -> str:
        prompt = (
            "You are a document summarizer. Provide a clear, comprehensive summary "
            "of the following document. Preserve key facts, figures, and conclusions. "
            "Use markdown formatting."
        )
        return self._call_llm(prompt, text)

    def _summarize_map_reduce(self, text: str) -> str:
        chunks = chunk_text(text)
        logger.info("Document split into %d chunks for map-reduce", len(chunks))

        # map phase: summarize each chunk
        chunk_prompt = (
            "Summarize this section of a larger document. "
            "Preserve key facts, figures, and important details."
        )
        chunk_summaries = [self._call_llm(chunk_prompt, chunk) for chunk in chunks]

        # reduce phase: combine chunk summaries into final summary
        combined = "\n\n---\n\n".join(chunk_summaries)
        reduce_prompt = (
            "Below are summaries of different sections of the same document. "
            "Combine them into a single coherent summary. Use markdown formatting. "
            "Remove redundancy and organize logically."
        )
        return self._call_llm(reduce_prompt, combined)
