# Track 2: ADK Agent with MCP Tool Access

This project satisfies the Track 2 requirement from the public APAC GenAI Academy brief:
- implemented using Google ADK
- uses MCP to connect the agent to one tool / data source
- retrieves external data and uses it in the final response
- is prepared for Cloud Run deployment

Implemented use case:
- a travel-weather assistant that answers city weather questions using an MCP server
- the MCP server fetches live public weather data from Open-Meteo

Architecture
- `mcp_server.py` runs a stdio MCP server
- `track2_agent/agent.py` connects to that server through `McpToolset`
- `api.py` exposes a simple HTTP endpoint for the submission demo

API
- `GET /healthz`
- `POST /weather-brief`

Example request:

```bash
curl -X POST http://127.0.0.1:8080/weather-brief \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Singapore",
    "question": "Should I carry an umbrella this afternoon?"
  }'
```

Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
uvicorn api:app --host 0.0.0.0 --port 8080
```

If you prefer the Gemini Developer API instead of Vertex AI, set `GOOGLE_API_KEY` and omit the Vertex-specific variables.

Cloud Run deployment example

```bash
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/track2-mcp-weather
gcloud run deploy track2-mcp-weather \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/track2-mcp-weather \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=us-central1,TRACK2_MODEL=gemini-2.5-flash
```

Suggested submission artifacts
- Cloud Run URL
- Git repository URL
- one screenshot showing the agent answer grounded in live weather data
