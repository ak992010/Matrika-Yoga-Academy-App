# Track 3: AlloyDB Natural-Language Query App

This project satisfies the Track 3 requirement from the public APAC GenAI Academy brief:
- uses AlloyDB for PostgreSQL
- uses a custom dataset instead of the default lab dataset
- uses AlloyDB AI natural language to convert natural language into SQL
- executes the generated SQL and returns meaningful results

Use case sentence:
- exploring customer support tickets for a SaaS help desk

Note:
- AlloyDB AI natural language is currently a Pre-GA feature

Custom dataset:
- `helpdesk.organizations`
- `helpdesk.support_tickets`

Files:
- `sql/01_schema.sql`: creates the custom dataset and comments
- `sql/02_seed.sql`: loads sample support-ticket records
- `sql/03_nl_setup.sql`: installs `alloydb_ai_nl`, creates the configuration, registers the schema, and generates schema context

API:
- `GET /healthz`
- `GET /sample-questions`
- `POST /query`

## Quick Setup

The fastest path for this repo is:
1. Create an AlloyDB cluster and primary instance in the Google Cloud console.
2. Turn on public IP for the primary instance so Cloud Shell can reach it through the AlloyDB Auth Proxy.
3. Enable the `alloydb_ai_nl.enabled` database flag.
4. Grant the AlloyDB service agent the `roles/aiplatform.user` role.
5. Connect from Cloud Shell, run the SQL files in this repo, and then start the API.

Before you begin:

```bash
export PROJECT_ID="your-project-id"
gcloud config set project "$PROJECT_ID"
gcloud services enable alloydb.googleapis.com aiplatform.googleapis.com
```

### 1. Create the cluster and primary instance

Use the AlloyDB console flow to create a cluster and a primary instance. For a sandbox or demo environment, keep the setup small and simple:
- one primary instance
- a small machine type
- public IP enabled on the primary instance
- PostgreSQL 16 or 17

If you already have an instance, you can update the required flag and public IP with `gcloud`:

```bash
export REGION="us-central1"
export CLUSTER_ID="track3-cluster"
export INSTANCE_ID="track3-primary"

gcloud alloydb instances update "$INSTANCE_ID" \
  --cluster="$CLUSTER_ID" \
  --region="$REGION" \
  --database-flags=alloydb_ai_nl.enabled=on \
  --assign-inbound-public-ip=ASSIGN_IPV4 \
  --no-async
```

If you are creating a fresh instance with `gcloud`, make sure your cluster networking is already set up for AlloyDB, then create the primary instance with the same flag enabled:

```bash
gcloud alloydb instances create "$INSTANCE_ID" \
  --cluster="$CLUSTER_ID" \
  --region="$REGION" \
  --instance-type=PRIMARY \
  --cpu-count=2 \
  --availability-type=ZONAL \
  --database-flags=alloydb_ai_nl.enabled=on \
  --assign-inbound-public-ip=ASSIGN_IPV4
```

### 2. Grant Vertex AI access to the AlloyDB service agent

AlloyDB AI natural language uses Vertex AI behind the scenes. Bind the `Vertex AI User` role to the AlloyDB service agent:

```bash
export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-alloydb.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

The IAM change can take a few minutes to propagate.

### 3. Connect from Cloud Shell with the AlloyDB Auth Proxy

Cloud Shell already includes `alloydb-auth-proxy` and `psql`. In the Google Cloud console:
1. Open your AlloyDB cluster.
2. Find the primary instance.
3. Click **View connectivity configuration**.
4. Copy the connection URI.

Then, in one Cloud Shell tab:

```bash
alloydb-auth-proxy "YOUR_CONNECTION_URI" --public-ip
```

Leave that process running. In a second Cloud Shell tab, clone or open this repo and connect with `psql`:

```bash
export PGPASSWORD="your-postgres-password"

psql "host=127.0.0.1 user=postgres dbname=postgres port=5432"
```

### 4. Load the custom dataset and NL configuration

From the repo root for this project:

```bash
export PGURI="postgresql://postgres:${PGPASSWORD}@127.0.0.1:5432/postgres"

psql "$PGURI" -f sql/01_schema.sql
psql "$PGURI" -f sql/02_seed.sql
psql "$PGURI" -f sql/03_nl_setup.sql
```

`sql/03_nl_setup.sql` installs `alloydb_ai_nl`, creates the `support_helpdesk_nl_config` configuration, registers the `helpdesk` schema, and applies generated schema context.

### 5. Run the API

You can run the API either in Cloud Shell or on any machine that has a working path to the database.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql+psycopg://postgres:${PGPASSWORD}@127.0.0.1:5432/postgres"
export TRACK3_NL_CONFIG_ID="support_helpdesk_nl_config"
uvicorn api:app --host 0.0.0.0 --port 8080
```

If your app connects directly to an AlloyDB host instead of a local Auth Proxy, replace `127.0.0.1:5432` with the reachable AlloyDB endpoint.

### 6. Test the endpoint

```bash
curl -X POST http://127.0.0.1:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which premium customers have open billing tickets in Singapore?"
  }'
```

## Sample Questions

- Which premium customers have open billing tickets in Singapore?
- Show unresolved high-priority tickets assigned to Mira.
- Which organizations in Japan reported the lowest average CSAT?
- Count open technical tickets created after 2026-03-01.

## Deployment Note

The current Docker image only runs the FastAPI app. It does not bundle the AlloyDB Auth Proxy or any VPC wiring.

For Cloud Run, add one of the documented AlloyDB connectivity patterns before relying on the deployment:
- private IP with Direct VPC egress
- public IP with the AlloyDB Auth Proxy or a language connector

A plain host-based `DATABASE_URL` is only enough when the runtime already has a valid network path to the AlloyDB instance.

## Suggested Submission Artifacts

- repository URL
- a screenshot or short demo video showing generated SQL and returned rows
- optional deployed URL if you expose the API publicly
