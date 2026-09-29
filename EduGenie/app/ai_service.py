import json
from typing import Any

from .config import settings


SYSTEM_INSTRUCTION = """
You are EduGenie, a friendly academic learning assistant.

Your purpose is to help students understand academic subjects.

Rules:

1. Use clear and simple language.
2. Explain concepts step by step.
3. Use examples whenever useful.
4. Do not invent facts.
5. If information is insufficient, clearly say so.
6. Prefer headings and bullet points.
7. Make explanations suitable for students.
8. For exam preparation, highlight important points.
9. Avoid unnecessarily complicated language.
"""


def get_client():
    """
    Create a Google Gemini client.
    """

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Create a .env file and add your Gemini API key."
        )

    from google import genai

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def generate(
    prompt: str,
    *,
    temperature: float = 0.4,
    json_mode: bool = False,
) -> str:
    """
    Send a prompt to Gemini and return the generated text.
    """

    from google.genai import types

    client = get_client()

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=temperature,
        response_mime_type=(
            "application/json"
            if json_mode
            else "text/plain"
        ),
    )

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=config,
    )

    text = getattr(
        response,
        "text",
        None,
    )

    if not text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return text.strip()


def chat(
    message: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """
    AI chatbot.
    """

    context = ""

    for item in (history or [])[-8:]:
        role = item.get(
            "role",
            "user",
        )

        content = item.get(
            "content",
            "",
        )

        context += (
            f"{role.upper()}: "
            f"{content}\n"
        )

    prompt = f"""
Conversation so far:

{context}

STUDENT:
{message}

EDUGENIE:
"""

    return generate(prompt)


def explain(
    topic: str,
    level: str = "beginner",
) -> str:
    """
    Explain a topic.
    """

    prompt = f"""
Explain the following topic to a
{level} level student:

TOPIC:
{topic}

Include:

1. Simple definition
2. Three key points
3. One real-life analogy
4. One small example
5. Short revision point
"""

    return generate(prompt)


def summarize(text: str) -> str:
    """
    Summarize study material.
    """

    prompt = f"""
Summarize the following study material.

Return these sections:

1. Overview
2. Key Points
3. Important Terms
4. Exam Revision Points
5. Five Flashcards

Preserve the original meaning.

STUDY MATERIAL:

{text}
"""

    return generate(
        prompt,
        temperature=0.2,
    )


def quiz(
    topic: str,
    count: int = 5,
    difficulty: str = "medium",
) -> list[dict[str, Any]]:
    """
    Generate multiple-choice questions.
    """

    count = max(
        1,
        min(count, 15),
    )

    prompt = f"""
Create exactly {count}
multiple-choice questions about:

{topic}

Difficulty:
{difficulty}

Return ONLY a JSON array.

Every question must contain:

question:
A string

options:
An array containing exactly four strings

answer:
A zero-based integer from 0 to 3

explanation:
A short explanation

Do not include Markdown.
"""

    raw = generate(
        prompt,
        temperature=0.7,
        json_mode=True,
    )

    try:
        data = json.loads(raw)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini returned invalid quiz JSON."
        ) from exc

    if not isinstance(data, list):
        raise ValueError(
            "Quiz response was not a JSON array."
        )

    cleaned = []

    for question in data[:count]:

        if not isinstance(question, dict):
            continue

        options = question.get(
            "options",
            [],
        )

        answer = question.get(
            "answer",
            0,
        )

        if not isinstance(options, list):
            continue

        if len(options) != 4:
            continue

        if not isinstance(answer, int):
            continue

        if answer < 0 or answer > 3:
            continue

        cleaned.append(
            {
                "question": str(
                    question.get(
                        "question",
                        "",
                    )
                ),
                "options": [
                    str(option)
                    for option in options
                ],
                "answer": answer,
                "explanation": str(
                    question.get(
                        "explanation",
                        "",
                    )
                ),
            }
        )

    if not cleaned:
        raise ValueError(
            "Gemini did not return valid quiz questions."
        )

    return cleaned


def learning_path(
    goal: str,
    level: str = "beginner",
    weeks: int = 4,
) -> str:
    """
    Generate a personalized learning roadmap.
    """

    weeks = max(
        1,
        min(weeks, 12),
    )

    prompt = f"""
Create a {weeks}-week learning roadmap.

Learning goal:
{goal}

Student level:
{level}

For every week provide:

1. Objectives
2. Topics
3. Practice activities
4. Small checkpoint

At the end include:

Suggested daily routine
"""

    return generate(prompt)