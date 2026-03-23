Matrika Academy App
Fresh Streamlit rebuild for the academy experience: dashboard, programs, schedule, admissions, live studio, certification, kids studio, payments, and contact.

What it includes
- A new visual system with a warm academy-style layout
- Sidebar navigation with quick actions
- Forms for admissions, attendance, payments, kids enquiries, certification, and contact
- Razorpay payment-link checkout inside the payments page, with manual UPI fallback
- Google Sheets persistence for cloud deployments, with local CSV fallback for development
- Admin page for reviewing saved entries after password unlock
- Live Studio page for links, replays, and attendance tracking
- Optional logo support via `assets/matrika_logo.svg`
- SEO landing page, `robots.txt`, and `sitemap.xml` support through `seo_server.py`

Run it
```bash
cd /Users/abhinavkashyappeddamandadi/Documents/matrika_yoga_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Run the SEO wrapper locally
```bash
cd /Users/abhinavkashyappeddamandadi/Documents/matrika_yoga_app
source .venv/bin/activate
APP_BASE_PATH=/app uvicorn seo_server:app --host 0.0.0.0 --port 8501
```

That local wrapper gives you:
- `/` as a crawlable academy landing page
- `/robots.txt`
- `/sitemap.xml`
- `/app` as the Streamlit academy app

Data from the forms is written into `submissions/` locally. On Streamlit Community Cloud, add Google Sheets secrets so submissions persist across restarts.

Deploy to Render
1. Create a new Render Blueprint or Web Service from this repo.
2. Render can read the placeholders in `render.yaml` automatically.
3. Add these environment variables in Render:
   - `GOOGLE_SHEET_ID`
   - `GOOGLE_SERVICE_ACCOUNT_JSON`
   - `ADMIN_PASSWORD`
   - `RESEND_API_KEY`
   - `RESEND_FROM_EMAIL`
   - `SMTP_HOST`
   - `SMTP_PORT`
   - `SMTP_USERNAME`
   - `SMTP_PASSWORD`
   - `SMTP_FROM_EMAIL`
   - `SMTP_FROM_NAME`
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
4. After the first deploy, add your custom domain in Render and point your registrar DNS records to the values Render shows.
5. Redirect your secondary domain to the primary domain after HTTPS is active.
6. The Render service now serves an SEO-friendly landing page at `/` and the Streamlit app at `/app`, which is much better for Google indexing than exposing only the Streamlit shell.

Deploy to Streamlit Community Cloud
1. Push this folder to a GitHub repository.
2. In Streamlit Community Cloud, create a new app from that repo and point it at `app.py`.
3. Add these secrets in the Streamlit Cloud secrets manager:
```toml
google_sheet_id = "your-google-sheet-id"
admin_password = "choose-a-strong-password"
resend_api_key = "re_your_resend_api_key"
resend_from_email = "Matrika Academy <onboarding@resend.dev>"
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_username = "your-email@gmail.com"
smtp_password = "your-app-password"
smtp_from_email = "your-email@gmail.com"
smtp_from_name = "Matrika Academy"
razorpay_key_id = "rzp_live_your_key_id"
razorpay_key_secret = "your-razorpay-key-secret"

[google_service_account_json]
type = "service_account"
project_id = "your-project-id"
private_key_id = "replace-me"
private_key = """-----BEGIN PRIVATE KEY-----
REPLACE_ME
-----END PRIVATE KEY-----
"""
client_email = "service-account@your-project.iam.gserviceaccount.com"
client_id = "replace-me"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/service-account"
```
4. Share the Google Sheet with the service account email from the JSON file.
5. Redeploy the app. The sidebar will show whether persistent Google Sheets storage is active.
6. Open the `Admin` page in the app and unlock it with `admin_password` to review submissions.
7. Add `resend_api_key` and `resend_from_email` if you want automatic confirmation emails and password reset codes to use HTTPS delivery, which works better on hosts that block SMTP.
8. Or add the SMTP secrets if you specifically want SMTP delivery after form submissions.
9. Add the Razorpay secrets if you want the payment page to generate hosted Razorpay checkout links.

Google Sheets setup checklist
1. Create a Google Sheet that will hold the form data.
2. Copy the sheet ID from the browser URL.
3. Create a Google Cloud service account with Google Sheets API access.
4. Download the service account JSON key.
5. Share the Google Sheet with the `client_email` from that JSON file.
6. Paste the values into Streamlit secrets using `.streamlit/secrets.example.toml` as the template.
7. Open the deployed app, submit one test form, then confirm the row appears in the Google Sheet and the `Admin` page.

Admin tools
- The `Admin` page can be protected with `admin_password`.
- It shows storage status, counts per submission source, recent rows, and a CSV download for the selected form.
- When Google Sheets is active, it also shows a direct button to open the connected spreadsheet.

Confirmation emails
- Every form with an email field can send a confirmation email to the same address after submission.
- The app now supports HTTPS email delivery through Resend, which is the recommended option on Render.
- For Gmail, use `smtp.gmail.com` with port `587` and a Gmail app password.
- On free Render web services, outbound SMTP ports are blocked, so Resend is the better production choice there.
- If email secrets are missing, submissions still save normally and the app shows a setup hint instead of failing.

Razorpay checkout
- The payments page can generate hosted Razorpay Payment Links for the signed-in learner account.
- Add `razorpay_key_id` and `razorpay_key_secret` in Streamlit secrets or host environment variables.
- The app stores each generated payment link in the `razorpay_links` worksheet / `razorpay_links.csv` so the team can track status in admin.
- Learners can still use the older direct UPI and manual payment-proof path as a fallback.
