from __future__ import annotations

import csv
import html
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import streamlit as st

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "submissions"
DATA_DIR.mkdir(exist_ok=True)
LOGO_PATH = APP_DIR / "assets" / "matrika_logo.png"
LIVE_ZOOM_URL = "https://us04web.zoom.us/j/8048675666?pwd=KF3fzQ5y1ZaDibDafMrbWHyCHl2jqV.1"
BACKUP_MEET_URL = ""
REPLAY_DRIVE_URL = ""
PAYMENT_UPI_ID = "pdr14@ybl"
PAYMENT_UPI_URL = f"upi://pay?pa={PAYMENT_UPI_ID}&pn=Matrika%20Academy&cu=INR"
CONTACT_PHONE = "7893939545"
CONTACT_EMAIL = "drpeddamandadi@gmail.com"
GOOGLE_SHEETS_SCOPE = ("https://www.googleapis.com/auth/spreadsheets",)
GOOGLE_SERVICE_ACCOUNT_SECRET = "google_service_account_json"
GOOGLE_SHEET_ID_SECRET = "google_sheet_id"
ADMIN_PASSWORD_SECRET = "admin_password"

PAGE_NAMES = [
    "Dashboard",
    "Programs",
    "Schedule",
    "Admissions",
    "Live Studio",
    "Certification",
    "Kids Studio",
    "Payments",
    "Contact",
    "Admin",
]

HOME_STATS = [
    {
        "label": "Live batches / week",
        "value": "6",
        "note": "Morning and evening sessions",
    },
    {
        "label": "Average cohort",
        "value": "12",
        "note": "Small groups, personal attention",
    },
    {
        "label": "Core tracks",
        "value": "5",
        "note": "Motherhood, kids, and teachers",
    },
    {
        "label": "Support mode",
        "value": "Live + replay",
        "note": "Easy to join from anywhere",
    },
]

PROGRAM_CARDS = [
    {
        "kicker": "Motherhood",
        "title": "Garbhasanskara Flow",
        "body": "Breath, affirmation, and gentle mobility for a calm pregnancy practice.",
        "meta": ["Trimester-safe", "Live + replay", "Mentored"],
    },
    {
        "kicker": "Recovery",
        "title": "Prenatal + Postnatal Care",
        "body": "Practical sequences for comfort before delivery and support after birth.",
        "meta": ["Healing", "Small batch", "Flexible timing"],
    },
    {
        "kicker": "Children",
        "title": "Kids Yoga Studio",
        "body": "Stories, balance games, and breath work that keep children engaged.",
        "meta": ["Ages 5-14", "Fun + calm", "Parent updates"],
    },
    {
        "kicker": "Teachers",
        "title": "Certification Path",
        "body": "Practice teaching, sequencing, adjustments, and supervised feedback.",
        "meta": ["Mentored", "Certificate", "Practicum"],
    },
    {
        "kicker": "Foundation",
        "title": "Everyday Wellness",
        "body": "A beginner-friendly path for breathing, posture, and routine building.",
        "meta": ["Beginners", "Weekend friendly", "Replay access"],
    },
]

FEATURE_CARDS = [
    {
        "kicker": "Care",
        "title": "Safety-first sequencing",
        "body": "Classes are organized with stage-appropriate movement and gentle cueing.",
        "meta": ["Clear guidance", "Low pressure"],
    },
    {
        "kicker": "Access",
        "title": "Live links and replays",
        "body": "Everything needed to join a class or catch up later is kept in one place.",
        "meta": ["Zoom / Meet", "On demand"],
    },
    {
        "kicker": "Growth",
        "title": "Mentored teacher journey",
        "body": "Future teachers get feedback, practicum blocks, and clear completion milestones.",
        "meta": ["Teaching circles", "Specialization"],
    },
]

SCHEDULE_HIGHLIGHTS = [
    {
        "kicker": "Monday / Wednesday",
        "title": "Morning grounding",
        "body": "Slow breath, mobility, and reset work for a fresh start.",
        "meta": ["07:00 AM", "All levels"],
    },
    {
        "kicker": "Tuesday / Thursday",
        "title": "Evening flow",
        "body": "A guided class for working parents and busy learners.",
        "meta": ["06:30 PM", "Live"],
    },
    {
        "kicker": "Friday / Saturday",
        "title": "Specialty sessions",
        "body": "Kids studio, recovery work, and mentor practice depending on the week.",
        "meta": ["Replay friendly", "Small group"],
    },
]

WEEKLY_SCHEDULE = [
    {
        "Day": "Mon",
        "Time": "07:00 AM",
        "Track": "Garbhasanskara",
        "Focus": "Grounding breath",
    },
    {
        "Day": "Tue",
        "Time": "06:30 PM",
        "Track": "Trimester Flow",
        "Focus": "Mobility + comfort",
    },
    {
        "Day": "Wed",
        "Time": "07:00 AM",
        "Track": "Prenatal Practice",
        "Focus": "Strength + ease",
    },
    {
        "Day": "Thu",
        "Time": "06:30 PM",
        "Track": "Postnatal Recovery",
        "Focus": "Core + balance",
    },
    {
        "Day": "Fri",
        "Time": "05:30 PM",
        "Track": "Kids Yoga",
        "Focus": "Stories + movement",
    },
    {
        "Day": "Sat",
        "Time": "10:00 AM",
        "Track": "Teacher Certification",
        "Focus": "Practicum + feedback",
    },
]

ADMISSIONS_STEPS = [
    {
        "title": "Share your goal",
        "body": "Tell us your stage, schedule, and what support you need.",
    },
    {
        "title": "We suggest the best fit",
        "body": "Our team recommends the right batch, replay path, or specialty track.",
    },
    {
        "title": "Join the first session",
        "body": "You receive the live link, onboarding details, and any notes you need.",
    },
]

CERTIFICATION_STEPS = [
    {
        "title": "Foundation",
        "body": "Learn the Matrika method, class structure, and cueing language.",
    },
    {
        "title": "Practice",
        "body": "Teach small segments, receive feedback, and refine your flow.",
    },
    {
        "title": "Specialize",
        "body": "Add prenatal, postnatal, or child yoga focus with guided mentorship.",
    },
    {
        "title": "Complete",
        "body": "Finish the practicum and receive your certificate of completion.",
    },
]

CERT_METRICS = [
    {
        "label": "Mentorship",
        "value": "40+ hrs",
        "note": "Guided feedback and support",
    },
    {
        "label": "Practicum blocks",
        "value": "6",
        "note": "Teach, review, refine",
    },
    {
        "label": "Specialization",
        "value": "Prenatal + Kids",
        "note": "Grow into a focused teacher",
    },
    {
        "label": "Outcome",
        "value": "Certificate",
        "note": "Issued on completion",
    },
]

KIDS_METRICS = [
    {
        "label": "Age band",
        "value": "5-14",
        "note": "Small groups with parent updates",
    },
    {
        "label": "Format",
        "value": "Live online",
        "note": "Simple, playful, and safe",
    },
    {
        "label": "Learning feel",
        "value": "Story-led",
        "note": "Keeps attention engaged",
    },
]

PAYMENT_PLANS = [
    {
        "kicker": "Entry plan",
        "title": "Garbhasanskara (4 weeks)",
        "body": "Gentle live support for pregnant learners with replay access.",
        "meta": ["INR 4,200", "4 weeks", "Replay included"],
    },
    {
        "kicker": "Monthly",
        "title": "Trimester Flow",
        "body": "A monthly rhythm for comfort, mobility, and steady practice.",
        "meta": ["INR 3,500", "Monthly", "Live sessions"],
    },
    {
        "kicker": "Bundle",
        "title": "Prenatal / Postnatal",
        "body": "Eight guided sessions with practical recovery support.",
        "meta": ["INR 3,200", "8 sessions", "Small batch"],
    },
    {
        "kicker": "Kids",
        "title": "Kids Yoga",
        "body": "Playful classes designed for focus, balance, and calm.",
        "meta": ["INR 2,800", "Monthly", "Ages 5-14"],
    },
    {
        "kicker": "Professional",
        "title": "Teacher Certification",
        "body": "A full pathway with theory, practicum, and mentored feedback.",
        "meta": ["INR 24,000", "Certification", "Mentorship"],
    },
]

CONTACT_CARDS = [
    {
        "kicker": "Phone",
        "title": CONTACT_PHONE,
        "body": "Best for admissions, batch timing, and live class updates.",
        "meta": ["Call or WhatsApp"],
    },
    {
        "kicker": "Email",
        "title": CONTACT_EMAIL,
        "body": "Best for admissions, receipts, and general questions.",
        "meta": ["24-48 hour reply"],
    },
    {
        "kicker": "UPI",
        "title": PAYMENT_UPI_ID,
        "body": "Use this handle for fee payments and quick confirmation.",
        "meta": ["Instant payment", "Fees"],
    },
]

st.set_page_config(
    page_title="Matrika Academy",
    page_icon="🪷",
    layout="wide",
    initial_sidebar_state="expanded",
)


def esc(value: object) -> str:
    return html.escape(str(value))


def normalize_text(value: str) -> str:
    return " ".join(str(value).split()).strip()


def normalize_email(value: str) -> str:
    return normalize_text(value).lower()


def digits_only(value: str) -> str:
    return "".join(character for character in str(value) if character.isdigit())


def normalize_phone(value: str) -> str:
    digits = digits_only(value)
    if not digits:
        return ""
    if len(digits) == 10:
        return f"+91{digits}"
    if digits.startswith("91") and len(digits) == 12:
        return f"+{digits}"
    return digits


def valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


def valid_phone(value: str) -> bool:
    digits = digits_only(value)
    if not digits:
        return False
    return len(digits) == 10 or (digits.startswith("91") and len(digits) == 12)


def build_whatsapp_url(message: str) -> str:
    return f"https://wa.me/{digits_only(normalize_phone(CONTACT_PHONE))}?text={quote(message)}"


def build_mailto_url(subject: str, body: str) -> str:
    return f"mailto:{CONTACT_EMAIL}?subject={quote(subject)}&body={quote(body)}"


def render_support_actions(subject: str, message: str, *, include_call: bool = True) -> None:
    columns = st.columns(3 if include_call else 2)
    with columns[0]:
        st.link_button(
            "WhatsApp the team",
            build_whatsapp_url(message),
            use_container_width=True,
        )
    if include_call:
        with columns[1]:
            st.link_button(
                "Call the team",
                f"tel:{normalize_phone(CONTACT_PHONE)}",
                use_container_width=True,
            )
        email_slot = columns[2]
    else:
        email_slot = columns[1]
    with email_slot:
        st.link_button(
            "Email the team",
            build_mailto_url(subject, message),
            use_container_width=True,
        )


def google_persistence_enabled() -> bool:
    return bool(st.secrets.get(GOOGLE_SERVICE_ACCOUNT_SECRET, "")) and bool(
        st.secrets.get(GOOGLE_SHEET_ID_SECRET, "")
    )


def get_google_spreadsheet():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return None

    raw_secret = st.secrets.get(GOOGLE_SERVICE_ACCOUNT_SECRET, "")
    sheet_id = st.secrets.get(GOOGLE_SHEET_ID_SECRET, "")
    if not raw_secret or not sheet_id:
        return None

    if isinstance(raw_secret, dict):
        service_account_info = raw_secret
    else:
        service_account_info = json.loads(raw_secret)

    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=list(GOOGLE_SHEETS_SCOPE),
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(str(sheet_id))


def append_row_to_google_sheet(csv_name: str, row: dict) -> bool:
    if not google_persistence_enabled():
        return False

    spreadsheet = get_google_spreadsheet()
    if spreadsheet is None:
        return False

    worksheet_name = Path(csv_name).stem
    import gspread

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=max(20, len(row) + 2),
        )

    if not worksheet.get_all_values():
        worksheet.append_row(list(row.keys()), value_input_option="RAW")
    worksheet.append_row([str(row[key]) for key in row.keys()], value_input_option="RAW")
    return True


def admin_password_configured() -> bool:
    return bool(str(st.secrets.get(ADMIN_PASSWORD_SECRET, "")).strip())


def admin_authenticated() -> bool:
    return bool(st.session_state.get("admin_authenticated", False))


def list_submission_sources() -> list[str]:
    names = {path.name for path in DATA_DIR.glob("*.csv")}
    if google_persistence_enabled():
        sheet_names = [
            "bookings.csv",
            "attendance.csv",
            "training_applications.csv",
            "kids_enquiries.csv",
            "payments.csv",
            "contact_messages.csv",
        ]
        names.update(sheet_names)
    return sorted(names)


def read_local_rows(csv_name: str) -> list[dict[str, str]]:
    file_path = DATA_DIR / csv_name
    if not file_path.exists():
        return []
    with file_path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_google_rows(csv_name: str) -> list[dict[str, str]]:
    if not google_persistence_enabled():
        return []
    spreadsheet = get_google_spreadsheet()
    if spreadsheet is None:
        return []

    import gspread

    worksheet_name = Path(csv_name).stem
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        return []
    values = worksheet.get_all_records()
    return [{str(key): str(value) for key, value in row.items()} for row in values]


def load_submission_rows(csv_name: str) -> list[dict[str, str]]:
    google_rows = read_google_rows(csv_name)
    if google_rows:
        return google_rows
    return read_local_rows(csv_name)


def storage_status_lines() -> list[str]:
    lines = []
    if google_persistence_enabled():
        lines.append("Google Sheets persistence is active.")
    else:
        lines.append("Google Sheets persistence is not configured yet.")
        lines.append(
            f"Add `{GOOGLE_SHEET_ID_SECRET}` and `{GOOGLE_SERVICE_ACCOUNT_SECRET}` in Streamlit secrets."
        )
    if admin_password_configured():
        lines.append("Admin password is configured.")
    else:
        lines.append(f"Add `{ADMIN_PASSWORD_SECRET}` in Streamlit secrets to protect the admin page.")
    return lines


def save_row(csv_name: str, row: dict) -> None:
    file_path = DATA_DIR / csv_name
    if google_persistence_enabled():
        try:
            append_row_to_google_sheet(csv_name, row)
        except Exception as exc:
            st.warning(f"Google Sheets sync failed for {csv_name}: {exc}")

    exists = file_path.exists()
    with file_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=row.keys())
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def jump_to(page: str) -> None:
    st.session_state.page = page


def chips(items: list[str] | tuple[str, ...]) -> str:
    return "".join(f"<span class='meta-chip'>{esc(item)}</span>" for item in items)


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #fffaf4;
            --bg-soft: #f4eae0;
            --ink: #2d2330;
            --muted: #6b5d67;
            --rose: #c86f8b;
            --rose-strong: #a85977;
            --gold: #cf9866;
            --sage: #8fa68f;
            --line: rgba(96, 72, 84, 0.16);
            --card: rgba(255, 255, 255, 0.82);
            --shadow: 0 18px 45px rgba(57, 38, 49, 0.12);
        }

        * {
            box-sizing: border-box;
        }

        html,
        body,
        [class*="css"] {
            font-family: "Manrope", sans-serif;
            color: var(--ink);
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 18%, rgba(200, 111, 139, 0.16), transparent 25%),
                radial-gradient(circle at 84% 8%, rgba(143, 166, 143, 0.18), transparent 23%),
                radial-gradient(circle at 50% 100%, rgba(207, 152, 102, 0.14), transparent 28%),
                linear-gradient(180deg, var(--bg) 0%, var(--bg-soft) 100%);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        #MainMenu,
        footer {
            visibility: hidden;
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 2.25rem;
        }

        h1,
        h2,
        h3,
        h4 {
            font-family: "Cormorant Garamond", serif;
            color: var(--ink);
            letter-spacing: 0.01em;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(255, 250, 245, 0.96), rgba(246, 234, 225, 0.94));
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.1rem;
            padding-bottom: 1.2rem;
        }

        .sidebar-card,
        .hero-card,
        .feature-card,
        .info-card,
        .schedule-card,
        .pricing-card,
        .timeline-card,
        .contact-card,
        .metric-card,
        .page-intro,
        .callout {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 24px;
            box-shadow: var(--shadow);
        }

        .sidebar-card {
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }

        .sidebar-brand img {
            width: 64px;
            height: 64px;
            border-radius: 18px;
            object-fit: cover;
            box-shadow: 0 12px 26px rgba(117, 79, 92, 0.16);
        }

        .sidebar-brand h2 {
            margin: 0;
            font-size: 1.6rem;
            line-height: 1;
        }

        .sidebar-brand p,
        .sidebar-note,
        .page-copy,
        .hero-copy,
        .card-copy,
        .metric-note {
            color: var(--muted);
        }

        .sidebar-brand p {
            margin: 0.25rem 0 0;
            font-size: 0.92rem;
        }

        .sidebar-note {
            margin-top: 0.5rem;
            font-size: 0.92rem;
            line-height: 1.55;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 999px;
            background: rgba(200, 111, 139, 0.12);
            color: var(--rose-strong);
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            padding: 0.38rem 0.7rem;
        }

        .hero-card {
            position: relative;
            overflow: hidden;
            padding: clamp(1.4rem, 3vw, 2.2rem);
        }

        .hero-card::after {
            content: "";
            position: absolute;
            inset: auto -10% -28% auto;
            width: 280px;
            height: 280px;
            border-radius: 50%;
            background: radial-gradient(
                circle,
                rgba(200, 111, 139, 0.24) 0%,
                rgba(200, 111, 139, 0.08) 50%,
                transparent 72%
            );
            pointer-events: none;
        }

        .hero-title {
            margin: 0.55rem 0 0.85rem;
            font-size: clamp(2.4rem, 5.8vw, 4.8rem);
            line-height: 0.92;
            max-width: 11ch;
        }

        .hero-copy {
            max-width: 62ch;
            font-size: 1.02rem;
            line-height: 1.7;
        }

        .hero-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
            margin-top: 1rem;
        }

        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid var(--line);
            color: #53444d;
            font-weight: 700;
            font-size: 0.86rem;
            padding: 0.42rem 0.76rem;
        }

        .page-intro {
            padding: 1.15rem 1.2rem 1.1rem;
            margin-bottom: 1rem;
        }

        .page-intro h1 {
            margin: 0.5rem 0 0.35rem;
            font-size: clamp(2rem, 4vw, 3.5rem);
            line-height: 0.95;
        }

        .page-copy {
            margin: 0;
            max-width: 70ch;
            line-height: 1.7;
        }

        .section-heading {
            margin: 2rem 0 1rem;
        }

        .section-heading h2 {
            margin: 0.45rem 0 0.35rem;
            font-size: clamp(1.9rem, 3.1vw, 2.65rem);
            line-height: 1;
        }

        .section-heading p {
            margin: 0;
            max-width: 72ch;
            line-height: 1.65;
            color: var(--muted);
        }

        .feature-card,
        .info-card,
        .schedule-card,
        .pricing-card,
        .timeline-card,
        .contact-card {
            position: relative;
            overflow: hidden;
            padding: 1rem 1rem 1.05rem;
        }

        .feature-card::before,
        .info-card::before,
        .schedule-card::before,
        .pricing-card::before,
        .timeline-card::before,
        .contact-card::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: linear-gradient(180deg, var(--rose), var(--gold));
        }

        .card-kicker {
            color: var(--rose-strong);
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
            font-weight: 800;
            margin-bottom: 0.45rem;
        }

        .feature-card h3,
        .info-card h3,
        .schedule-card h3,
        .pricing-card h3,
        .timeline-card h3,
        .contact-card h3 {
            margin: 0 0 0.45rem;
            font-size: 1.55rem;
            line-height: 1;
        }

        .card-copy {
            margin: 0;
            line-height: 1.65;
        }

        .meta-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.85rem;
        }

        .meta-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            background: rgba(143, 166, 143, 0.12);
            color: #4f6252;
            padding: 0.36rem 0.64rem;
            font-size: 0.78rem;
            font-weight: 700;
        }

        .metric-card {
            padding: 1rem;
        }

        .metric-label {
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.72rem;
            font-weight: 800;
        }

        .metric-value {
            margin: 0.2rem 0 0.2rem;
            font-family: "Cormorant Garamond", serif;
            font-size: 2rem;
            line-height: 1;
        }

        .metric-note {
            font-size: 0.92rem;
            line-height: 1.5;
        }

        .timeline {
            display: grid;
            gap: 0.7rem;
        }

        .timeline-step {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 0.9rem;
            align-items: start;
            padding: 0.95rem 1rem;
            border-radius: 22px;
            background: rgba(255, 255, 255, 0.7);
            border: 1px solid var(--line);
            box-shadow: 0 10px 24px rgba(63, 42, 51, 0.06);
        }

        .timeline-index {
            width: 2.15rem;
            height: 2.15rem;
            border-radius: 999px;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, var(--rose), var(--gold));
            color: white;
            font-weight: 800;
            flex-shrink: 0;
        }

        .timeline-step h4 {
            margin: 0 0 0.2rem;
            font-size: 1.2rem;
            line-height: 1.1;
        }

        .timeline-step p {
            margin: 0;
            color: var(--muted);
            line-height: 1.55;
        }

        .callout {
            border-radius: 22px;
            border: 1px solid rgba(200, 111, 139, 0.22);
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(247, 235, 225, 0.8));
            padding: 1rem 1.1rem;
            box-shadow: 0 14px 28px rgba(63, 42, 51, 0.08);
        }

        .stButton > button {
            border-radius: 999px;
            border: 1px solid transparent;
            background: linear-gradient(135deg, var(--rose), var(--gold));
            color: white;
            font-weight: 800;
            padding: 0.68rem 1rem;
            box-shadow: 0 12px 24px rgba(200, 111, 139, 0.24);
            transition: transform 0.18s ease, filter 0.18s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            filter: brightness(0.98);
        }

        [data-testid="stLinkButton"] a {
            border-radius: 999px !important;
            border: 1px solid var(--line) !important;
            background: rgba(255, 255, 255, 0.82) !important;
            color: var(--ink) !important;
            font-weight: 800 !important;
            box-shadow: 0 10px 20px rgba(63, 42, 51, 0.08) !important;
        }

        hr {
            border-color: rgba(96, 72, 84, 0.12);
        }

        @media (max-width: 980px) {
            .hero-title {
                max-width: none;
            }
        }

        @media (max-width: 760px) {
            .sidebar-brand h2 {
                font-size: 1.45rem;
            }

            .hero-title {
                font-size: clamp(2.05rem, 11vw, 3.2rem);
            }

            .page-intro h1,
            .section-heading h2 {
                font-size: clamp(1.8rem, 9vw, 2.6rem);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_card(
    title: str,
    body: str,
    *,
    kicker: str | None = None,
    meta: list[str] | tuple[str, ...] | None = None,
    class_name: str = "feature-card",
) -> None:
    kicker_html = f"<div class='card-kicker'>{esc(kicker)}</div>" if kicker else ""
    meta_html = f"<div class='meta-row'>{chips(list(meta or []))}</div>" if meta else ""
    st.markdown(
        f"""
        <div class="{class_name}">
            {kicker_html}
            <h3>{esc(title)}</h3>
            <p class="card-copy">{esc(body)}</p>
            {meta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_card_grid(
    items: list[dict[str, object]],
    *,
    columns: int = 3,
    class_name: str = "feature-card",
) -> None:
    if not items:
        return

    columns = max(1, min(columns, len(items)))
    slots = st.columns(columns)
    for index, item in enumerate(items):
        with slots[index % columns]:
            render_card(
                str(item.get("title", "")),
                str(item.get("body", "")),
                kicker=str(item["kicker"]) if item.get("kicker") else None,
                meta=list(item.get("meta", [])) if item.get("meta") else None,
                class_name=class_name,
            )


def render_metric_grid(metrics: list[dict[str, str]]) -> None:
    slots = st.columns(len(metrics))
    for slot, metric in zip(slots, metrics):
        with slot:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{esc(metric["label"])}</div>
                    <div class="metric-value">{esc(metric["value"])}</div>
                    <div class="metric-note">{esc(metric["note"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_steps(steps: list[dict[str, str]]) -> None:
    for index, step in enumerate(steps, start=1):
        st.markdown(
            f"""
            <div class="timeline-step">
                <div class="timeline-index">{index:02d}</div>
                <div>
                    <h4>{esc(step["title"])}</h4>
                    <p>{esc(step["body"])}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_section(eyebrow: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="section-heading">
            <span class="eyebrow">{esc(eyebrow)}</span>
            <h2>{esc(title)}</h2>
            <p>{esc(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        st.markdown(
            """
            <div class="sidebar-card">
                <div class="sidebar-brand">
                    <div>
                        <h2>Matrika Academy</h2>
                        <p>Live classes, kids yoga, and teacher training.</p>
                    </div>
                </div>
                <div class="sidebar-note">
                    Calm, structured, and easy to navigate for families and trainees.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.radio(
            "Navigate",
            PAGE_NAMES,
            key="page",
            label_visibility="collapsed",
        )

        st.markdown(
            """
            <div class="sidebar-card">
                <div class="card-kicker">Quick actions</div>
                <p class="card-copy">Jump straight to the most common parts of the app.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Book admission",
            key="sidebar_book",
            use_container_width=True,
            on_click=jump_to,
            args=("Admissions",),
        )
        st.button(
            "Open live studio",
            key="sidebar_live",
            use_container_width=True,
            on_click=jump_to,
            args=("Live Studio",),
        )
        st.button(
            "View payments",
            key="sidebar_payments",
            use_container_width=True,
            on_click=jump_to,
            args=("Payments",),
        )

        st.markdown(
            f"""
            <div class="sidebar-card">
                <div class="card-kicker">Support</div>
                <p class="card-copy">Email: {CONTACT_EMAIL}</p>
                <p class="card-copy">Phone: {CONTACT_PHONE}</p>
                <p class="card-copy">Timing: IST batches</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button(
            "WhatsApp the team",
            build_whatsapp_url(
                "Hi Matrika Academy, I want help with admissions, class timings, or payments."
            ),
            use_container_width=True,
        )
        st.link_button(
            "Email the team",
            build_mailto_url(
                "Matrika Academy enquiry",
                "Hi Matrika Academy, I want help with admissions, class timings, or payments.",
            ),
            use_container_width=True,
        )

        storage_message = (
            "Persistent Google Sheets storage is connected."
            if google_persistence_enabled()
            else "Local CSV fallback is active. Add Google Sheets secrets to keep cloud submissions persistent."
        )
        st.markdown(
            f"""
            <div class="sidebar-card">
                <div class="card-kicker">Storage</div>
                <p class="card-copy">{storage_message}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def dashboard_page() -> None:
    left, right = st.columns([1.35, 0.95])
    with left:
        st.markdown(
            """
            <div class="hero-card">
                <span class="eyebrow">Matrika Academy</span>
                <h1 class="hero-title">A calm app for learning, practice, and growth.</h1>
                <p class="hero-copy">
                    Keep classes, admissions, replays, fees, and mentorship in one place for
                    mothers, children, and future teachers.
                </p>
                <div class="pill-row">
                    <span class="pill">Small cohorts</span>
                    <span class="pill">Replay support</span>
                    <span class="pill">Mentored teachers</span>
                    <span class="pill">Live online</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
        actions = st.columns(3)
        with actions[0]:
            st.button(
                "Browse programs",
                key="dash_programs",
                use_container_width=True,
                on_click=jump_to,
                args=("Programs",),
            )
        with actions[1]:
            st.button(
                "Book a trial",
                key="dash_admissions",
                use_container_width=True,
                on_click=jump_to,
                args=("Admissions",),
            )
        with actions[2]:
            st.button(
                "Open live studio",
                key="dash_live",
                use_container_width=True,
                on_click=jump_to,
                args=("Live Studio",),
            )

    with right:
        next_session = WEEKLY_SCHEDULE[0]
        render_card(
            f'{next_session["Day"]} · {next_session["Time"]}',
            f'{next_session["Track"]} - {next_session["Focus"]}',
            kicker="Next live class",
            meta=["Live", "IST", "Small batch"],
            class_name="info-card",
        )
        st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
        render_card(
            "Support promise",
            "Every enquiry is saved and reviewed by the Matrika team so the next step stays clear.",
            kicker="Human follow-through",
            meta=["Admissions", "Phone", "Email"],
            class_name="info-card",
        )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    render_metric_grid(HOME_STATS)

    render_section(
        "Featured tracks",
        "A practical view of the main learning paths offered inside the academy.",
        "Each track is built to feel calm, structured, and easy to join.",
    )
    render_card_grid(PROGRAM_CARDS[:4], columns=2)

    render_section(
        "What makes Matrika feel different",
        "Three simple principles shape the experience from the first session onward.",
        "The app should feel warm, direct, and human - not overloaded.",
    )
    render_card_grid(FEATURE_CARDS, columns=3)

    render_section(
        "How the journey works",
        "The academy flow is simple enough for first-time learners and structured enough for long-term growth.",
        "Use this as the path from enquiry to ongoing practice.",
    )
    render_steps(ADMISSIONS_STEPS)


def programs_page() -> None:
    render_section(
        "Academy tracks",
        "Structured journeys for every stage of learning.",
        "From pregnancy support to playful children's classes and mentoring for future teachers, the app keeps every path clear.",
    )
    render_card_grid(PROGRAM_CARDS, columns=3)

    st.divider()
    render_section(
        "Class structure",
        "A good academy app should show both the path and the outcome.",
        "This table can be extended with timings, batch numbers, or pricing later.",
    )
    st.dataframe(
        [
            {
                "Program": "Garbhasanskara Flow",
                "Duration": "4-6 weeks",
                "Outcome": "Pregnancy support and breath awareness",
            },
            {
                "Program": "Prenatal + Postnatal Care",
                "Duration": "8 sessions",
                "Outcome": "Comfort, recovery, and consistency",
            },
            {
                "Program": "Kids Yoga Studio",
                "Duration": "Monthly",
                "Outcome": "Focus, balance, and calm routines",
            },
            {
                "Program": "Certification Path",
                "Duration": "Full cohort",
                "Outcome": "Teaching confidence and practicum",
            },
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.info("If you want a different batch structure, the admissions form is the place to request it.")


def schedule_page() -> None:
    render_section(
        "Weekly calendar",
        "A rhythm that feels steady instead of crowded.",
        "All timings are in IST and the schedule is designed for live participation with replay access.",
    )
    render_card_grid(SCHEDULE_HIGHLIGHTS, columns=3, class_name="schedule-card")
    st.divider()

    left, right = st.columns([1.2, 0.8])
    with left:
        render_section("Weekly timetable", "Current live slots at a glance.", "This view can be swapped for a richer calendar later.")
        st.dataframe(WEEKLY_SCHEDULE, use_container_width=True, hide_index=True)
    with right:
        render_card(
            "Replay support",
            "Missed a class? The replay library keeps the learning moving without adding stress.",
            kicker="Flexibility",
            meta=["On demand", "Missed class friendly"],
            class_name="info-card",
        )
        st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
        render_card(
            "Time zone",
            "All sessions are shown in IST so learners know exactly when to join.",
            kicker="Location",
            meta=["India Standard Time", "Global access"],
            class_name="info-card",
        )


def admissions_page() -> None:
    render_section(
        "Admissions",
        "Book a trial, ask a question, or request a custom batch.",
        "Use this form to start the onboarding flow. The team will confirm by email or phone.",
    )
    left, right = st.columns([0.95, 1.05])
    with left:
        render_card(
            "What happens next",
            "We review the request, suggest the right track, and share the live link or replay path once enrollment is confirmed.",
            kicker="Admissions",
            meta=["Friendly review", "Quick reply", "Small batch"],
            class_name="timeline-card",
        )
        st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
        render_steps(ADMISSIONS_STEPS)
        st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
        render_support_actions(
            "Matrika Academy admission enquiry",
            "Hi Matrika Academy, I want help choosing the right program and batch.",
        )

    with right:
        with st.form("booking_form"):
            full_name = st.text_input("Full name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            track = st.selectbox(
                "Track",
                [
                    "Garbhasanskara Flow",
                    "Prenatal + Postnatal Care",
                    "Kids Yoga Studio",
                    "Certification Path",
                    "Everyday Wellness",
                ],
            )
            learner_stage = st.selectbox(
                "Learner stage",
                [
                    "First-time learner",
                    "Returning learner",
                    "Prenatal",
                    "Postnatal",
                    "Child",
                    "Teacher trainee",
                ],
            )
            mode = st.selectbox("Preferred mode", ["Live", "Replay", "Hybrid"])
            preferred_time = st.selectbox("Preferred time", ["Morning", "Afternoon", "Evening"])
            goals = st.text_area("What would you like help with?")
            notes = st.text_area("Health notes / availability (optional)")
            submit = st.form_submit_button("Request admission")

            if submit:
                clean_name = normalize_text(full_name)
                clean_email = normalize_email(email)
                clean_phone = normalize_phone(phone)
                clean_goals = normalize_text(goals)
                clean_notes = normalize_text(notes)

                if not clean_name or not clean_email:
                    st.error("Name and email are required.")
                elif not valid_email(clean_email):
                    st.error("Enter a valid email address.")
                elif phone and not valid_phone(phone):
                    st.error("Enter a valid phone number or leave it blank.")
                else:
                    save_row(
                        "bookings.csv",
                        {
                            "submitted_at": datetime.now().isoformat(timespec="seconds"),
                            "page": "Admissions",
                            "name": clean_name,
                            "email": clean_email,
                            "phone": clean_phone,
                            "track": track,
                            "learner_stage": learner_stage,
                            "mode": mode,
                            "preferred_time": preferred_time,
                            "goals": clean_goals,
                            "notes": clean_notes,
                        },
                    )
                    st.success("Your request was saved. We will contact you shortly.")


def live_studio_page() -> None:
    render_section(
        "Live studio",
        "Join live sessions, access replays, and record attendance.",
        "This area keeps the live teaching experience organized and easy to revisit.",
    )
    live_tab, replay_tab, attendance_tab = st.tabs(["Live access", "Replays", "Attendance"])

    with live_tab:
        left, right = st.columns(2)
        with left:
            render_card(
                "Join today's class",
                "Use the main link for the live session and keep the backup link ready if your connection changes.",
                kicker="Live links",
                meta=["Zoom", "Primary link", "IST"],
                class_name="info-card",
            )
            st.link_button("Open live Zoom", LIVE_ZOOM_URL)
            if BACKUP_MEET_URL:
                st.link_button("Open backup Meet", BACKUP_MEET_URL)
            else:
                st.link_button(
                    "Request backup link",
                    build_whatsapp_url(
                        "Hi Matrika Academy, please share the backup live class link for today."
                    ),
                    use_container_width=True,
                )
                st.caption("Use WhatsApp if the primary link does not open.")
        with right:
            render_card(
                "Live etiquette",
                "Arrive five minutes early, keep your camera on if you are comfortable, and use chat for questions.",
                kicker="Quick guide",
                meta=["Arrive early", "Mute when needed", "Use chat"],
                class_name="info-card",
            )

    with replay_tab:
        left, right = st.columns(2)
        with left:
            render_card(
                "Replay library",
                "Recent recordings stay available for learners who missed a live class or want another practice round.",
                kicker="Library",
                meta=["On demand", "Missed class friendly"],
                class_name="info-card",
            )
            st.markdown(
                """
                - Garbhasanskara grounding flow
                - Prenatal mobility flow
                - Kids storytime calm
                """,
                unsafe_allow_html=True,
            )
            if REPLAY_DRIVE_URL:
                st.link_button("Open replay drive", REPLAY_DRIVE_URL)
            else:
                st.link_button(
                    "Request replay access",
                    build_whatsapp_url(
                        "Hi Matrika Academy, please share the latest replay access link."
                    ),
                    use_container_width=True,
                )
                st.caption("The team can share the replay link on WhatsApp or email.")
        with right:
            render_card(
                "Class resources",
                "Weekly notes, class reminders, and simple practice guides can live here as the app grows.",
                kicker="Materials",
                meta=["Weekly notes", "Practice guides", "Class links"],
                class_name="info-card",
            )

    with attendance_tab:
        with st.form("attendance_form"):
            attendee_name = st.text_input("Name")
            attendee_email = st.text_input("Email")
            session = st.selectbox(
                "Session",
                ["Garbhasanskara", "Trimester", "Prenatal", "Postnatal", "Kids", "Teacher Training"],
            )
            mode = st.selectbox("Mode", ["Live", "Replay"])
            submit = st.form_submit_button("Save attendance")

            if submit:
                clean_name = normalize_text(attendee_name)
                clean_email = normalize_email(attendee_email)

                if not clean_name or not clean_email:
                    st.error("Name and email are required.")
                elif not valid_email(clean_email):
                    st.error("Enter a valid email address.")
                else:
                    save_row(
                        "attendance.csv",
                        {
                            "submitted_at": datetime.now().isoformat(timespec="seconds"),
                            "page": "Live Studio",
                            "name": clean_name,
                            "email": clean_email,
                            "session": session,
                            "mode": mode,
                        },
                    )
                    st.success("Attendance saved.")


def certification_page() -> None:
    render_section(
        "Certification",
        "Mentored training for future Matrika teachers.",
        "This pathway blends practice teaching, feedback loops, and specialty work with mothers and children.",
    )
    render_metric_grid(CERT_METRICS)
    st.divider()

    left, right = st.columns([1, 1])
    with left:
        render_section("Program flow", "A simple path from foundation to certification.", "Each step is designed to build confidence.")
        render_steps(CERTIFICATION_STEPS)
    with right:
        render_card(
            "What is included",
            "Sequencing and class planning, prenatal and postnatal specialization, practice teaching circles, and a completion certificate.",
            kicker="Program scope",
            meta=["Practicum", "Specialization", "Certificate"],
            class_name="timeline-card",
        )
        st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
        with st.form("training_form"):
            full_name = st.text_input("Full name")
            email = st.text_input("Email")
            experience = st.selectbox(
                "Experience",
                ["Beginner", "Practitioner (1+ yr)", "Intermediate", "Advanced"],
            )
            motivation = st.text_area("Why do you want to teach?")
            submit = st.form_submit_button("Apply")

            if submit:
                clean_name = normalize_text(full_name)
                clean_email = normalize_email(email)
                clean_motivation = normalize_text(motivation)

                if not clean_name or not clean_email:
                    st.error("Name and email are required.")
                elif not valid_email(clean_email):
                    st.error("Enter a valid email address.")
                else:
                    save_row(
                        "training_applications.csv",
                        {
                            "submitted_at": datetime.now().isoformat(timespec="seconds"),
                            "page": "Certification",
                            "name": clean_name,
                            "email": clean_email,
                            "experience": experience,
                            "motivation": clean_motivation,
                        },
                    )
                    st.success("Application received. Mentors will reach out.")


def kids_page() -> None:
    render_section(
        "Kids studio",
        "Movement, stories, and calm-down breath for ages 5-14.",
        "The experience is designed to keep children engaged without feeling rushed or overwhelmed.",
    )
    render_metric_grid(KIDS_METRICS)
    st.divider()
    render_card_grid(
        [
            {
                "kicker": "Stories",
                "title": "Movement with imagination",
                "body": "Each class uses playful stories and simple themes to keep children engaged.",
                "meta": ["Narrative-led", "Easy to follow"],
            },
            {
                "kicker": "Balance",
                "title": "Coordination and focus",
                "body": "Safe balance work, gentle stretching, and body awareness build confidence.",
                "meta": ["Calm body", "Strong focus"],
            },
            {
                "kicker": "Calm down",
                "title": "Breath for home time",
                "body": "Children finish with breath, rest, and a simple takeaway they can use at home.",
                "meta": ["Family-friendly", "Short practice"],
            },
        ],
        columns=3,
        class_name="schedule-card",
    )

    st.divider()
    with st.form("kids_form"):
        parent = st.text_input("Parent / Guardian name")
        child = st.text_input("Child name")
        age = st.number_input("Child age", min_value=3, max_value=18, step=1)
        email = st.text_input("Contact email")
        submit = st.form_submit_button("Enroll or enquire")

        if submit:
            clean_parent = normalize_text(parent)
            clean_child = normalize_text(child)
            clean_email = normalize_email(email)

            if not clean_parent or not clean_child or not clean_email:
                st.error("Parent name, child name, and email are required.")
            elif not valid_email(clean_email):
                st.error("Enter a valid email address.")
            else:
                save_row(
                    "kids_enquiries.csv",
                    {
                        "submitted_at": datetime.now().isoformat(timespec="seconds"),
                        "page": "Kids Studio",
                        "parent": clean_parent,
                        "child": clean_child,
                        "age": age,
                        "email": clean_email,
                    },
                )
                st.success("Enquiry received. We will share the kids schedule and links.")


def payments_page() -> None:
    render_section(
        "Tuition and payments",
        "Choose a plan and share proof when you are ready.",
        "The app keeps payment steps simple and transparent so the team can confirm your seat quickly.",
    )
    render_card_grid(PAYMENT_PLANS, columns=3, class_name="pricing-card")
    st.divider()

    left, right = st.columns([1.15, 0.85])
    with left:
        payment_actions = st.columns(2)
        with payment_actions[0]:
            st.link_button("Open UPI payment", PAYMENT_UPI_URL, use_container_width=True)
        with payment_actions[1]:
            st.link_button(
                "WhatsApp payment proof",
                build_whatsapp_url(
                    "Hi Matrika Academy, I want to share my payment confirmation."
                ),
                use_container_width=True,
            )
        st.code(PAYMENT_UPI_ID)
        st.caption("If the UPI button does not open on desktop, pay to this UPI ID inside your UPI app.")
    with right:
        render_card(
            "Need an invoice?",
            f"Email {CONTACT_EMAIL} with your selected plan and GST details.",
            kicker="Billing",
            meta=["Invoice support", "GST ready"],
            class_name="info-card",
        )

    st.divider()
    render_section("Share payment proof", "Upload your payment reference so the team can verify it.", "Saved entries go to a CSV file for easy review.")
    with st.form("payment_form"):
        full_name = st.text_input("Name")
        email = st.text_input("Email")
        plan = st.selectbox("Plan", [item["title"] for item in PAYMENT_PLANS])
        amount = st.number_input("Amount paid (INR)", min_value=500, max_value=100000, step=100)
        method = st.selectbox("Method", ["UPI", "Card", "NetBanking", "Wallet"])
        reference = st.text_input("Payment reference / UPI transaction ID")
        notes = st.text_area("Notes (batch, time, coupon)")
        submit = st.form_submit_button("Submit proof")

        if submit:
            clean_name = normalize_text(full_name)
            clean_email = normalize_email(email)
            clean_reference = normalize_text(reference)
            clean_notes = normalize_text(notes)

            if not clean_name or not clean_email or not clean_reference:
                st.error("Name, email, and payment reference are required.")
            elif not valid_email(clean_email):
                st.error("Enter a valid email address.")
            else:
                save_row(
                    "payments.csv",
                    {
                        "submitted_at": datetime.now().isoformat(timespec="seconds"),
                        "page": "Payments",
                        "name": clean_name,
                        "email": clean_email,
                        "plan": plan,
                        "amount": amount,
                        "method": method,
                        "reference": clean_reference,
                        "notes": clean_notes,
                    },
                )
                st.success("Payment recorded. We will verify and confirm your seat.")


def contact_page() -> None:
    render_section(
        "Connect",
        "Reach the team by email, phone, or the form below.",
        "We keep replies friendly and quick so families and teachers always know the next step.",
    )
    render_card_grid(CONTACT_CARDS, columns=3, class_name="contact-card")
    st.divider()

    left, right = st.columns([0.95, 1.05])
    with left:
        render_card(
            "Support details",
            "Studio mode is 100% online, with IST-based classes and replay support.",
            kicker="Quick facts",
            meta=["Zoom / Meet", "IST batches", "Replay support"],
            class_name="info-card",
        )
        st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
        render_support_actions(
            "Matrika Academy support",
            "Hi Matrika Academy, I need help with classes, payments, or admissions.",
        )
    with right:
        with st.form("contact_form"):
            full_name = st.text_input("Name")
            email = st.text_input("Email")
            message = st.text_area("Message")
            submit = st.form_submit_button("Send message")

            if submit:
                clean_name = normalize_text(full_name)
                clean_email = normalize_email(email)
                clean_message = normalize_text(message)

                if not clean_name or not clean_email or not clean_message:
                    st.error("Please complete all fields.")
                elif not valid_email(clean_email):
                    st.error("Enter a valid email address.")
                else:
                    save_row(
                        "contact_messages.csv",
                        {
                            "submitted_at": datetime.now().isoformat(timespec="seconds"),
                            "page": "Contact",
                            "name": clean_name,
                            "email": clean_email,
                            "message": clean_message,
                        },
                    )
                    st.success("Message sent. We will reply soon.")


def admin_page() -> None:
    render_section(
        "Admin",
        "See submission flow, storage status, and recent entries.",
        "This view is meant for the Matrika team to monitor enquiries and confirm that persistence is working.",
    )

    if not admin_authenticated():
        render_card(
            "Protected area",
            "Enter the admin password to view stored enquiries, payments, and attendance records.",
            kicker="Access",
            meta=["Password required"],
            class_name="info-card",
        )
        if not admin_password_configured():
            st.warning(
                f"The admin page is not fully protected yet. Add `{ADMIN_PASSWORD_SECRET}` in Streamlit secrets."
            )
        with st.form("admin_login_form"):
            password = st.text_input("Admin password", type="password")
            submit = st.form_submit_button("Unlock admin")
            if submit:
                expected = str(st.secrets.get(ADMIN_PASSWORD_SECRET, "")).strip()
                if not expected:
                    st.error("Admin password is not configured in Streamlit secrets yet.")
                elif password == expected:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect admin password.")
        return

    top_actions = st.columns([0.75, 0.25])
    with top_actions[1]:
        if st.button("Lock admin", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.rerun()

    render_card(
        "Storage status",
        "Use this view to confirm that cloud persistence and admin protection are set up correctly.",
        kicker="Status",
        meta=storage_status_lines(),
        class_name="info-card",
    )

    submission_files = list_submission_sources()
    total_rows = sum(len(load_submission_rows(name)) for name in submission_files)
    metrics = [
        {
            "label": "Submission sources",
            "value": str(len(submission_files)),
            "note": "Forms currently tracked",
        },
        {
            "label": "Saved rows",
            "value": str(total_rows),
            "note": "Across all forms",
        },
        {
            "label": "Persistence",
            "value": "Google Sheets" if google_persistence_enabled() else "Local CSV",
            "note": "Current primary storage",
        },
    ]
    render_metric_grid(metrics)
    st.divider()

    if not submission_files:
        st.info("No submission files exist yet. Once users start sending forms, they will appear here.")
        return

    selected_file = st.selectbox("Submission source", submission_files)
    rows = load_submission_rows(selected_file)

    if not rows:
        st.info(f"No entries found in `{selected_file}` yet.")
        return

    st.caption(f"{len(rows)} saved entries in `{selected_file}`")
    st.dataframe(rows[::-1], use_container_width=True, hide_index=True)


PAGE_ROUTES = {
    "Dashboard": dashboard_page,
    "Programs": programs_page,
    "Schedule": schedule_page,
    "Admissions": admissions_page,
    "Live Studio": live_studio_page,
    "Certification": certification_page,
    "Kids Studio": kids_page,
    "Payments": payments_page,
    "Contact": contact_page,
    "Admin": admin_page,
}


def initialize_state() -> None:
    st.session_state.setdefault("page", PAGE_NAMES[0])
    if st.session_state.page not in PAGE_NAMES:
        st.session_state.page = PAGE_NAMES[0]


def main() -> None:
    apply_theme()
    initialize_state()
    render_sidebar()
    PAGE_ROUTES[st.session_state.page]()


if __name__ == "__main__":
    main()
