# Track 2: BigQuery MCP Toolbox Lab

This starter maps the Google codelab "MCP Toolbox for Databases: Making BigQuery datasets available to MCP clients" into a local project you can run from this workspace.

It uses:
- MCP Toolbox for Databases as the MCP server
- BigQuery public dataset `bigquery-public-data.google_cloud_release_notes.release_notes`
- Google ADK for the client agent
- the ADK `toolbox` extra for the current Toolbox integration

## Files

- `tools.yaml`: Toolbox config that exposes `search_release_notes_bq` in toolset `my_bq_toolset`
- `gcp_releasenotes_agent_app/agent.py`: ADK agent that connects to Toolbox over HTTP
- `.env.example`: environment variables for Vertex AI and local Toolbox settings
- `scripts/download_toolbox.sh`: downloads a pinned Toolbox binary for your OS and CPU

## Prerequisites

- Python 3.11+
- `gcloud` CLI
- A Google Cloud project with billing enabled
- Application Default Credentials for BigQuery access

## Quick Start

```bash
cd /Users/abhinavkashyappeddamandadi/Documents/apac_genaiacademy_projects/track2_bigquery_mcp_toolbox
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and replace `your-project-id` with your actual Google Cloud project.

Load the environment and create Application Default Credentials:

```bash
set -a
source .env
set +a
gcloud auth application-default login
```

Download the Toolbox binary:

```bash
./scripts/download_toolbox.sh
```

Start Toolbox in one terminal:

```bash
source .venv/bin/activate
set -a
source .env
set +a
./toolbox --tools-file tools.yaml
```

You can verify that the server loaded the toolset by opening:

- `http://127.0.0.1:5000/ui`
- `http://127.0.0.1:5000/api/toolset`

Start the ADK agent in a second terminal:

```bash
cd /Users/abhinavkashyappeddamandadi/Documents/apac_genaiacademy_projects/track2_bigquery_mcp_toolbox
source .venv/bin/activate
set -a
source .env
set +a
adk run gcp_releasenotes_agent_app
```

Example prompt:

```text
Get me the latest Google Cloud release notes from the last 7 days.
```

## Notes

- The BigQuery dataset is public, but query jobs still run under your billing project.
- `BIGQUERY_LOCATION` should stay `US` for this public dataset.
- If port `5000` is busy, start Toolbox on another port and update `TOOLBOX_URL` in `.env`.

Example alternate port:

```bash
./toolbox --tools-file tools.yaml --port 7000
```

Then set:

```bash
TOOLBOX_URL=http://127.0.0.1:7000
```

## Optional BigQuery Sanity Check

If you want to validate the dataset directly before starting Toolbox:

```bash
bq query --use_legacy_sql=false '
SELECT product_name, description, published_at
FROM `bigquery-public-data.google_cloud_release_notes.release_notes`
WHERE DATE(published_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY published_at DESC
LIMIT 10
'
```
