import json
import logging
import re
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)

# Cap input text to avoid exceeding llama3.2's ~4k-token context window.
# 8000 characters ≈ 2000 tokens (average 4 chars/token), leaving room for the prompt itself.
_MAX_TEXT_CHARS = 8000

_PROMPT_TEMPLATE = """You are an expert at extracting structured data from purchase order documents.

Extract the following information from the purchase order text below and return ONLY valid JSON with no additional text or markdown:

{{
  "vendor_name": "<vendor or supplier name, or null>",
  "po_number": "<purchase order number, or null>",
  "date": "<document date as YYYY-MM-DD string, or null>",
  "line_items": [
    {{
      "description": "<item description>",
      "quantity": <numeric quantity or null>,
      "unit": "<unit of measure string or null>",
      "unit_price": <numeric unit price or null>
    }}
  ]
}}

Purchase Order Text:
---
{text}
---

Return only the JSON object, no explanation."""


async def extract_po_data(text: str) -> dict:
    """Send PO text to Ollama and return extracted structured data."""
    settings = get_settings()
    prompt = _PROMPT_TEMPLATE.format(text=text[:_MAX_TEXT_CHARS])

    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            raw_text = result.get("response", "")
            return _parse_json_response(raw_text)
    except httpx.HTTPError as exc:
        logger.error("Ollama HTTP error: %s", exc)
        return {}
    except Exception as exc:
        logger.error("Unexpected error calling Ollama: %s", exc)
        return {}


def _parse_json_response(raw: str) -> dict:
    """Extract JSON object from LLM response, tolerating surrounding text."""
    # Try direct parse first
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    # Try to find a JSON block within the response
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    logger.warning("Could not parse JSON from LLM response: %s", raw[:200])
    return {}
