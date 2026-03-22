# Track 1: ADK Agent on Cloud Run

This project satisfies the Track 1 requirement from the public APAC GenAI Academy brief:
- implemented using Google ADK
- uses Gemini for inference
- exposes one clear task over HTTP
- is ready to deploy to Cloud Run

Implemented task:
- summarize raw notes into a concise executive summary

API
- `GET /healthz`
- `POST /summarize`

Example request:

```bash
curl -X POST http://127.0.0.1:8080/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Today we reviewed onboarding delays, two customers escalated billing issues, and the team agreed to move password reset fixes into this sprint.",
    "style": "bullets",
    "max_words": 60
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
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/track1-adk-summarizer
gcloud run deploy track1-adk-summarizer \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/track1-adk-summarizer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=us-central1,TRACK1_MODEL=gemini-2.5-flash
```

Suggested submission artifacts
- Cloud Run URL
- Git repository URL
- one screenshot of a successful `POST /summarize` response
