# Track 2: Location Intelligence ADK Agent with BigQuery and Google Maps MCP

This project builds a Google ADK agent that combines:

- the hosted BigQuery MCP server for structured business data analysis
- the hosted Google Maps MCP server for real-world place and route validation
- a FastAPI wrapper so the agent can be run locally or deployed to Cloud Run

The included sample scenario is a bakery site-selection workflow in Los Angeles. The BigQuery data is synthetic, but it is shaped to support realistic location intelligence questions such as:

- Which zip code has the strongest morning foot traffic?
- Is that neighborhood already saturated with bakeries?
- What is the premium price ceiling for a sourdough loaf?
- What revenue could a new location project from historical weekly sales patterns?
- Is the closest supplier reachable within a practical drive time?

## Architecture

- `track2_location_agent/agent.py` defines the ADK `LlmAgent`
- `track2_location_agent/tools.py` connects the agent to:
  - `https://bigquery.googleapis.com/mcp`
  - `https://mapstools.googleapis.com/mcp`
- `api.py` exposes a simple HTTP API for demos or Cloud Run
- `setup/setup_env.sh` enables services and creates the local `.env`
- `setup/setup_bigquery.sh` provisions the demo dataset in BigQuery

## API

- `GET /healthz`
- `POST /location-intelligence`

Example request:

```bash
curl -X POST http://127.0.0.1:8080/location-intelligence \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Los Angeles",
    "business_type": "high-end sourdough bakery",
    "question": "Find the best area for a fourth location with strong morning foot traffic, low direct bakery saturation, and a nearby Restaurant Depot."
  }'
```

## Local setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Google Cloud auth

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
```

If `gcloud` is not on your shell `PATH` in this workspace, the setup scripts also know how to use the bundled SDK under `Documents/tools/google-cloud-sdk`.

### 3. Create the `.env` file and enable services

```bash
chmod +x setup/setup_env.sh
./setup/setup_env.sh
```

This script:

- enables BigQuery, Vertex AI, Maps tooling, and API key services
- enables MCP access for BigQuery and Google Maps
- creates a restricted Maps API key for `mapstools.googleapis.com`
- writes the project `.env`

### 4. Provision the demo BigQuery dataset

```bash
chmod +x setup/setup_bigquery.sh
./setup/setup_bigquery.sh
```

This creates the `location_intelligence_demo` dataset with:

- `demographics`
- `foot_traffic`
- `bakery_prices`
- `sales_history_weekly`

### 5. Run the API

```bash
uvicorn api:app --host 0.0.0.0 --port 8080
```

### 6. Run with ADK Web

```bash
adk web
```

Run that command from this project directory. ADK will discover `track2_location_agent`.

## Sample prompts

- `Find the zip code with the strongest morning foot traffic for a premium bakery in Los Angeles.`
- `Check whether that area is saturated with bakeries or if it is better positioned near specialty coffee shops.`
- `What is the current premium ceiling for a sourdough loaf in the Los Angeles Metro area?`
- `Project December revenue for a new store using the best historical sourdough-performing location and a price of $18.`
- `Find the closest Restaurant Depot to the proposed neighborhood and verify whether the drive time is under 30 minutes.`

## Cloud Run deployment example

```bash
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/track2-location-intelligence
gcloud run deploy track2-location-intelligence \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/track2-location-intelligence \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=global,LOCATION_INTELLIGENCE_DATASET=location_intelligence_demo,LOCATION_INTELLIGENCE_MODEL=gemini-2.5-flash,MAPS_API_KEY=$MAPS_API_KEY
```

## Notes

- BigQuery MCP uses Application Default Credentials, so long-lived sessions may need `gcloud auth application-default login` again if the OAuth token expires.
- The agent rebuilds its BigQuery MCP connection per API request so refreshed credentials are picked up without restarting the service.
- The demo data is synthetic and optimized for the bakery site-selection storyline.
