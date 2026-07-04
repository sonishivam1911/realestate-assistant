"""Model routing — Chinese frontier on OpenRouter. Kimi optional for orchestration only."""

import os

# Research: cheapest with Exa web search
MODEL_RESEARCH = os.getenv("CMA_MODEL_RESEARCH", "deepseek/deepseek-v4-flash")

# Optional orchestrator — Kimi K2 is better at tool loops but ~6x pricier than Flash.
# Kimi does NOT include web search; still uses Exa ($0.005/search).
MODEL_ORCHESTRATOR = os.getenv("CMA_MODEL_ORCHESTRATOR", "deepseek/deepseek-v4-flash")

# Synthesis: stronger reasoning for client report
MODEL_SYNTHESIS = os.getenv("CMA_MODEL_SYNTHESIS", "deepseek/deepseek-v4-pro")

# Kimi alternative if you want tool-heavy orchestration:
# CMA_MODEL_ORCHESTRATOR=moonshotai/kimi-k2  ($0.57/$2.30 — use only if tool loops fail on Flash)

TIMEFRAME_MONTHS = int(os.getenv("CMA_TIMEFRAME_MONTHS", "3"))
DEFAULT_RADIUS_MILES = float(os.getenv("CMA_DEFAULT_RADIUS_MILES", "5"))
