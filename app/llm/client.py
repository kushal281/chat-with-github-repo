from typing import Protocol
import time

from google import genai
from google.genai import types

from app.config import settings


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class GeminiClient:
    def __init__(self, api_key: str, model: str):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        for attempt in range(3):
            try:
                resp = self._client.models.generate_content(
                    model=self._model,
                    contents=user,
                    config=types.GenerateContentConfig(system_instruction=system),
                )
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2**attempt)  # wait 1s, then 2s
        if not resp.text:
            reason = resp.candidates[0].finish_reason if resp.candidates else "no candidates"
            raise RuntimeError(f"Empty response from LLM (finish_reason={reason})")
        return resp.text


def get_llm() -> LLMClient:
    return GeminiClient(settings.llm_api_key, settings.llm_model)