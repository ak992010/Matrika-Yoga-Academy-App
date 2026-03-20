Matrika Academy App
Fresh Streamlit rebuild for the academy experience: dashboard, programs, schedule, admissions, live studio, certification, kids studio, payments, and contact.

What it includes
- A new visual system with a warm academy-style layout
- Sidebar navigation with quick actions
- Forms for admissions, attendance, payments, kids enquiries, certification, and contact
- Google Sheets persistence for cloud deployments, with local CSV fallback for development
- Admin page for reviewing saved entries after password unlock
- Live Studio page for links, replays, and attendance tracking
- Optional logo support via `assets/matrika_logo.png`

Run it
```bash
cd /Users/abhinavkashyappeddamandadi/Documents/matrika_yoga_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Data from the forms is written into `submissions/` locally. On Streamlit Community Cloud, add Google Sheets secrets so submissions persist across restarts.

Deploy to Streamlit Community Cloud
1. Push this folder to a GitHub repository.
2. In Streamlit Community Cloud, create a new app from that repo and point it at `app.py`.
3. Add these secrets in the Streamlit Cloud secrets manager:
```toml
google_sheet_id = "your-google-sheet-id"
google_service_account_json = """{...full Google service account JSON...}"""
admin_password = "choose-a-strong-password"
```
4. Share the Google Sheet with the service account email from the JSON file.
5. Redeploy the app. The sidebar will show whether persistent Google Sheets storage is active.
6. Open the `Admin` page in the app and unlock it with `admin_password` to review submissions.
