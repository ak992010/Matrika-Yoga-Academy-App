# Building AI Agents with ADK: The Foundation

This note explains the core Agent Development Kit (ADK) ideas using the two working examples already present in this repository:

- `track1_adk_cloud_run`: a focused summarization agent
- `track2_adk_mcp_weather`: a grounded weather agent that uses MCP

The goal is to make the architecture easy to reason about before adding more advanced patterns like multi-agent orchestration, persistent memory, or evaluation pipelines.

## Why ADK

Google's Agent Development Kit is a code-first framework for building, running, and deploying agents. The official docs describe ADK as flexible, modular, model-agnostic, and deployment-agnostic, with agents, tools, sessions, state, and runners as the main building blocks.

That matters because an agent application is more than a prompt. A usable system needs:

- an agent definition
- a runtime that can execute the agent
- a session layer that tracks context
- tools for real-world actions or data access
- an outer application layer, such as FastAPI, to expose the agent safely

ADK gives us the agent/runtime/session pieces. Our repository adds the HTTP service layer around them.

## The Smallest Useful Mental Model

The cleanest way to think about ADK in this repo is:

`User request -> FastAPI endpoint -> Runner -> root_agent -> optional tools -> final response`

That is the foundation.

In practical terms:

1. The API receives validated input.
2. We convert that input into a prompt or user message.
3. A `Runner` executes the ADK `root_agent`.
4. The agent may answer directly or call tools first.
5. The API returns the final text as JSON.

## Core ADK Primitives

### 1. `root_agent`

In the Python quickstart, Google notes that `root_agent` is the only required element of an ADK agent project. In this repo, both tracks define a `root_agent` with `LlmAgent`.

Track 1 uses a narrowly scoped summarizer:

```python
root_agent = LlmAgent(
    name="track1_summarizer_agent",
    model=MODEL_NAME,
    description="Summarizes long-form text into concise executive-ready takeaways.",
    instruction=(
        "You are a production summarization agent. "
        "Your only job is to summarize user-provided text. "
        "Do not invent facts, do not answer unrelated questions, and do not add a preamble. "
        "Return a clean summary in the style requested by the user prompt."
    ),
)
```

This is the first foundation rule: start with one sharp responsibility. A small, explicit agent is easier to test, explain, and deploy.

### 2. `Runner`

The `Runner` is the execution engine around the agent. It is the piece that actually runs the ADK flow for a user message.

In `track1_adk_cloud_run/api.py`, the pattern is:

```python
session_service = InMemorySessionService()
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
)
```

This is the second foundation rule: separate definition from execution.

- `root_agent` defines behavior
- `Runner` executes behavior

That separation becomes more important once the system grows into multi-agent flows or longer-lived sessions.

### 3. `SessionService`

ADK sessions track conversation history and state. In the official docs, `InMemorySessionService` is explicitly non-persistent, which means state is lost on restart.

That is exactly what both local examples use today, and it is a good fit for early development because it keeps setup simple:

```python
session_service = InMemorySessionService()
session = await session_service.create_session(app_name=APP_NAME, user_id=user_id)
```

This gives us a practical foundation:

- use `InMemorySessionService` for local testing and stateless demos
- switch to a persistent session backend when conversation continuity matters across restarts

### 4. Tools

Tools are how agents move beyond pure text generation. ADK treats tools as capabilities the agent can call when it needs outside information or an action.

The official docs describe tools as the way agents interact with external APIs, search, code execution, databases, or other services. In this repo, Track 2 shows the cleanest example of that idea.

### 5. MCP via `McpToolset`

Track 2 adds real-world grounding with MCP. The official MCP docs explain that `McpToolset` handles:

- connection management to the MCP server
- tool discovery
- exposure of those tools to the ADK agent
- proxying tool calls back to the server

Our Track 2 agent wires that in like this:

```python
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[str(MCP_SERVER_PATH)],
            env=dict(os.environ),
            cwd=str(BASE_DIR),
        )
    )
)

root_agent = LlmAgent(
    name="track2_mcp_weather_agent",
    model=MODEL_NAME,
    instruction=(
        "You are a travel weather assistant. "
        "Always use the MCP tool to retrieve live city weather data before answering. "
        "Ground every factual weather statement in the tool response. "
        "If the tool returns no data, explain that clearly instead of guessing."
    ),
    tools=[mcp_toolset],
)
```

This is the third foundation rule: use tools when the answer depends on external reality.

If the user needs live weather, prices, databases, or file operations, the agent should not rely only on the model. It should call a tool.

## What The Two Repo Examples Teach

### Track 1: The minimum production-shaped agent

Track 1 is the clean starter template.

What it gets right:

- one task only: summarize text
- one public API route for the main capability
- explicit prompt shaping in the API layer
- clear model selection through environment variables
- a runner and session service that match ADK's runtime pattern

Why this matters:

If you cannot explain the job of your agent in one sentence, it is usually too broad for a first version.

Track 1 succeeds because it draws a hard boundary:

- input: text, style, max words
- output: summary only
- failure mode: empty agent response becomes an HTTP error

This is a strong foundation for Cloud Run or any other service wrapper.

### Track 2: The minimum grounded agent

Track 2 shows the next step after a single-purpose agent: connect the agent to reality.

The MCP server in `mcp_server.py` does the external work:

- geocodes the city
- fetches forecast data from Open-Meteo
- returns structured weather fields

The ADK agent does the reasoning and response composition:

- asks the MCP tool for data
- interprets the structured output
- answers with a practical recommendation

This separation is important. The agent should reason; the tool should fetch facts.

That keeps the design understandable:

- tool layer: reliable data retrieval
- agent layer: natural-language synthesis
- API layer: request validation and response formatting

## The Foundation Architecture In This Repo

### Layer 1: Agent definition

This is where we define:

- the agent name
- the model
- the instruction
- optional tools

Files:

- `track1_adk_cloud_run/track1_adk_agent/agent.py`
- `track2_adk_mcp_weather/track2_agent/agent.py`

### Layer 2: Runtime execution

This is where we define:

- `Runner`
- `SessionService`
- the async event loop that collects the final response

Files:

- `track1_adk_cloud_run/api.py`
- `track2_adk_mcp_weather/api.py`

### Layer 3: External capabilities

This is where tools live.

For Track 2, that is the MCP server:

- `track2_adk_mcp_weather/mcp_server.py`

### Layer 4: Application boundary

This is the FastAPI layer that:

- validates request bodies with Pydantic
- creates the user-facing prompt
- calls the runner
- returns structured JSON

This outer layer matters because agents should not be your entire application. They should be one well-contained part of it.

## Build Order For New ADK Agents

When starting from scratch, this repo suggests a reliable build order:

1. Define one narrow user-facing job.
2. Create a `root_agent` with a strong instruction and a clear description.
3. Wrap it in a `Runner` plus a `SessionService`.
4. Put input validation in an API layer instead of leaving everything to the model.
5. Add tools only when the task needs external facts or actions.
6. Keep tool logic deterministic and structured.
7. Return one clean final response format.

If you follow that order, the system usually stays simple enough to debug.

## Foundation Design Rules

These are the practical rules that fall out of the two working examples:

- Give each agent one job before you give it many jobs.
- Put strict instructions inside the agent, not only in ad hoc prompts.
- Keep HTTP validation outside the model.
- Use tools for live facts and side effects.
- Keep tool outputs structured so the agent reasons over clean data.
- Start with in-memory sessions, but plan for persistent sessions if continuity matters.
- Treat the agent as a service component, not the whole product.

## What Comes After The Foundation

Once this base is solid, the natural next ADK steps are:

- workflow agents such as `SequentialAgent`, `ParallelAgent`, or `LoopAgent`
- persistent session storage instead of `InMemorySessionService`
- agent evaluation and tracing
- multi-agent delegation
- richer tool ecosystems such as search, databases, or code execution

I am intentionally not treating those as the foundation. They are powerful, but the first win comes from getting the single-agent runtime pattern right.

## Local File Map

Use these files as the concrete reference implementation:

- `track1_adk_cloud_run/track1_adk_agent/agent.py`
- `track1_adk_cloud_run/api.py`
- `track2_adk_mcp_weather/track2_agent/agent.py`
- `track2_adk_mcp_weather/api.py`
- `track2_adk_mcp_weather/mcp_server.py`

## Official References

- [ADK overview](https://google.github.io/adk-docs/)
- [Technical overview](https://google.github.io/adk-docs/get-started/about/)
- [Python quickstart](https://google.github.io/adk-docs/get-started/python/)
- [Agents overview](https://google.github.io/adk-docs/agents/)
- [LLM agents](https://google.github.io/adk-docs/agents/llm-agents/)
- [Agent runtime](https://google.github.io/adk-docs/runtime/)
- [Session state](https://google.github.io/adk-docs/sessions/state/)
- [MCP tools](https://google.github.io/adk-docs/tools-custom/mcp-tools/)
- [ADK Python repository](https://github.com/google/adk-python)

## Closing View

The foundation of an ADK project is not "use a big model and hope for the best." It is a clear runtime shape:

- a focused `root_agent`
- a `Runner` that executes it
- a `SessionService` that manages context
- tools only where reality is needed
- an application layer that keeps the interface safe and predictable

Track 1 shows the minimum useful pattern. Track 2 shows how that same pattern grows once live tools enter the system. That is the real foundation for building AI agents with ADK.
