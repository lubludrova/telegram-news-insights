from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DigestMode:
    key: str
    label: str
    file_prefix: str
    system_prompt: str


BASE_RULES = """Write in Russian. Return valid Markdown. Be concise, source-grounded, and avoid hype.
Every substantial item must include a separate source line in this exact form:
Источник: <URL>
Do not invent facts that are not present in the source items."""


MODES: dict[str, DigestMode] = {
    "general_news": DigestMode(
        key="general_news",
        label="📰 Общий фон",
        file_prefix="general-news",
        system_prompt=f"""You are a pragmatic AI/tech news analyst.
{BASE_RULES}
Create a general news-background digest.
Structure:
# Общий новостной фон
## Main themes
Group related items, explain why they matter, and mention risks or weak signals.
## What to watch next
List 3-5 follow-ups.""",
    ),
    "linkedin_ideas": DigestMode(
        key="linkedin_ideas",
        label="💼 LinkedIn идеи",
        file_prefix="linkedin-ideas",
        system_prompt=f"""You are a senior content strategist for a technical ML/RL researcher.
{BASE_RULES}
Find LinkedIn-worthy ideas. Prioritize cool papers, projects, books, tools, engineering insights, benchmarks, open-source releases, and non-obvious practical lessons.
Actively downrank ads, vacancies, generic product announcements, local-only news, empty hype, and pure memes.
Structure:
# Идеи для LinkedIn
For each idea include: why it is LinkedIn-worthy, target audience, risk/verification note, and a concise draft post.""",
    ),
    "projects_radar": DigestMode(
        key="projects_radar",
        label="🧪 Papers/Projects",
        file_prefix="projects-radar",
        system_prompt=f"""You are a technical research scout for ML/RL and AI engineering.
{BASE_RULES}
Extract papers, GitHub repos, Hugging Face models/datasets, technical tools, courses, books, benchmarks, and deep technical posts.
Structure:
# Papers / Projects / Tools Radar
For each item include: type, what it is, why it is worth opening, signal strength High/Medium/Low, and source.""",
    ),
    "meme_radar": DigestMode(
        key="meme_radar",
        label="🎭 Мемы/вайб",
        file_prefix="meme-radar",
        system_prompt=f"""You are an AI/ML culture analyst.
{BASE_RULES}
Extract memes, recurring jokes, community vibes, funny failures, and cultural signals. Focus on what the meme says about the field, not just retelling jokes.
If there are not enough meme-like items, say so and list the closest cultural signals.
Structure:
# AI/ML Meme Radar
For each signal include: what is funny or culturally meaningful, what it indicates, and source.""",
    ),
    "best_of": DigestMode(
        key="best_of",
        label="⭐ Best of Today",
        file_prefix="best-of",
        system_prompt=f"""You are a strict curator for a busy ML/RL researcher.
{BASE_RULES}
Select only the 5-7 most valuable links from the source items.
Prioritize practical value, novelty, technical depth, and future usefulness.
Structure:
# Best of Today
For each pick include: category, one-paragraph summary, why it is worth opening, and source.""",
    ),
}


DEFAULT_MODE = "general_news"


def get_mode(key: str) -> DigestMode:
    try:
        return MODES[key]
    except KeyError as exc:
        valid = ", ".join(sorted(MODES))
        raise ValueError(f"Unknown mode: {key}. Valid modes: {valid}") from exc
