"""Shared LLM client wrapper. All LLM calls go through here."""

import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text()


def ask(prompt: str, system: str = "", model: str = "claude-sonnet-4-20250514") -> str:
    """Send a single prompt to Claude and return the text response."""
    messages = [{"role": "user", "content": prompt}]
    kwargs: dict = {"model": model, "max_tokens": 4096, "messages": messages}
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text
