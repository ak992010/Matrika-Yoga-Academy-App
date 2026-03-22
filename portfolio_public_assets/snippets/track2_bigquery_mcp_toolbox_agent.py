from __future__ import annotations

import os

from google.adk.agents import LlmAgent
from google.adk.tools.toolbox_toolset import ToolboxToolset


MODEL_NAME = (
    os.getenv("TRACK2_MODEL")
    or os.getenv("GOOGLE_GENAI_MODEL")
    or "gemini-2.5-flash"
)
TOOLBOX_URL = os.getenv("TOOLBOX_URL", "http://127.0.0.1:5000")
TOOLBOX_TOOLSET = os.getenv("TOOLBOX_TOOLSET", "my_bq_toolset")

toolbox_toolset = ToolboxToolset(
    server_url=TOOLBOX_URL,
    toolset_name=TOOLBOX_TOOLSET,
)

root_agent = LlmAgent(
    name="gcp_releasenotes_agent",
    model=MODEL_NAME,
    description="Answers questions about recent Google Cloud release notes using BigQuery through MCP Toolbox.",
    instruction=(
        "You are a helpful Google Cloud release notes assistant. "
        "Always use the configured Toolbox tool before answering factual questions "
        "about Google Cloud release notes. "
        "Summarize the results clearly, include published dates when relevant, "
        "and say explicitly if the tool returns no rows."
    ),
    tools=[toolbox_toolset],
)
