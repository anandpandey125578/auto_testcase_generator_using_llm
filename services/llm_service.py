import base64
import json
import logging
import mimetypes
import os
from pathlib import Path
from urllib import request


PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

logger = logging.getLogger(__name__)


def _load_prompt(file_name):
    return (PROMPT_DIR / file_name).read_text(encoding="utf-8")


def _call_openai_chat(api_key, messages, model):
    logger.info("LLM request started (model=%s)", model)
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }

    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=60) as response:
        body = response.read().decode("utf-8")
        data = json.loads(body)

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        logger.exception("LLM response parse failed")
        raise ValueError("Invalid response from LLM provider.") from exc


def _extract_csv_block(text):
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            block = parts[1]
            return block.strip().lstrip("csv").strip()
    return text.strip()


def _image_to_data_url(image_path):
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/png"

    with open(image_path, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")

    return f"data:{mime_type};base64,{encoded}"


def generate_testcases(
    raw_text,
    image_sequence,
    image_paths,
    api_key,
    model_override=None,
):
    if not api_key:
        raise ValueError("Missing OpenAI API key.")
    if not raw_text.strip():
        raise ValueError("No extracted text available for LLM.")

    prompt = _load_prompt("testcase_prompt.txt")
    model = model_override or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    logger.info(
        "Generating testcases (model=%s, text_len=%s, images=%s)",
        model,
        len(raw_text),
        len(image_paths or []),
    )

    image_lines = [
        f"{item['index']}. {item['name']}" for item in (image_sequence or [])
    ]
    image_context = "\n".join(image_lines) if image_lines else "None"

    content_parts = [
        {
            "type": "text",
            "text": (
                f"Requirements text:\n{raw_text}\n\n"
                f"Image sequence (filenames in order):\n{image_context}\n"
            ),
        }
    ]

    for image_path in image_paths or []:
        content_parts.append(
            {
                "type": "image_url",
                "image_url": {"url": _image_to_data_url(image_path)},
            }
        )

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content_parts},
    ]

    response_text = _call_openai_chat(api_key, messages, model)
    return _extract_csv_block(response_text)


def test_connection(api_key, model_override=None):
    if not api_key:
        raise ValueError("Missing OpenAI API key.")

    model = model_override or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    messages = [
        {"role": "system", "content": "Return only the word OK."},
        {"role": "user", "content": "Ping"},
    ]

    response_text = _call_openai_chat(api_key, messages, model)
    if "ok" not in response_text.strip().lower():
        raise ValueError("Unexpected response from LLM provider.")

    return True


def generate_code_from_csv(
    csv_text,
    framework,
    image_sequence,
    image_paths,
    api_key,
    model_override=None,
):
    if not api_key:
        raise ValueError("Missing OpenAI API key.")
    if not csv_text.strip():
        raise ValueError("No validated CSV available for code generation.")

    prompt = _load_prompt("codegen_prompt.txt")
    model = model_override or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    logger.info(
        "Generating code (model=%s, csv_len=%s, images=%s, framework=%s)",
        model,
        len(csv_text),
        len(image_paths or []),
        framework,
    )

    image_lines = [
        f"{item['index']}. {item['name']}" for item in (image_sequence or [])
    ]
    image_context = "\n".join(image_lines) if image_lines else "None"

    content_parts = [
        {
            "type": "text",
            "text": (
                f"Framework: {framework}\n\n"
                f"CSV test cases:\n{csv_text}\n\n"
                f"Image sequence (filenames in order):\n{image_context}\n"
            ),
        }
    ]

    for image_path in image_paths or []:
        content_parts.append(
            {
                "type": "image_url",
                "image_url": {"url": _image_to_data_url(image_path)},
            }
        )

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content_parts},
    ]

    response_text = _call_openai_chat(api_key, messages, model)
    return response_text.strip()
