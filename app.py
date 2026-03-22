from __future__ import annotations

import base64
import csv
import hashlib
import html
import hmac
import io
import json
import os
import re
import secrets
import smtplib
import ssl
import time
from collections.abc import Mapping
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "submissions"
DATA_DIR.mkdir(exist_ok=True)
LOGO_PATH = APP_DIR / "assets" / "matrika_logo.svg"
BUDDHA_BACKGROUND_PATH = APP_DIR / "assets" / "buddha_meditation.svg"
LIVE_ZOOM_URL = "https://us04web.zoom.us/j/8048675666?pwd=KF3fzQ5y1ZaDibDafMrbWHyCHl2jqV.1"
BACKUP_MEET_URL = ""
REPLAY_DRIVE_URL = ""
PAYMENT_UPI_ID = "pdr14@ybl"
PAYMENT_UPI_URL = f"upi://pay?pa={PAYMENT_UPI_ID}&pn=Matrika%20Academy&cu=INR"
CONTACT_PHONE = "7893939545"
CONTACT_EMAIL = "drpeddamandadi@gmail.com"
APP_BASE_PATH = os.getenv("APP_BASE_PATH", "/").rstrip("/") or "/"
HOME_HREF = APP_BASE_PATH
PUBLIC_SITE_URL = os.getenv("PUBLIC_SITE_URL", "https://matrikayogaacademy.com").rstrip("/")
PUBLIC_SITE_HOST = re.sub(r"^https?://", "", PUBLIC_SITE_URL).rstrip("/")
RAZORPAY_API_BASE_URL = "https://api.razorpay.com"
GOOGLE_SHEETS_SCOPE = ("https://www.googleapis.com/auth/spreadsheets",)
GOOGLE_SERVICE_ACCOUNT_SECRET = "google_service_account_json"
GOOGLE_SHEET_ID_SECRET = "google_sheet_id"
ADMIN_PASSWORD_SECRET = "admin_password"
IST_ZONE = ZoneInfo("Asia/Kolkata")
OVERVIEW_WORKSHEET = "Sheet1"
SUBMISSION_COOLDOWN_SECONDS = 20
SMTP_HOST_SECRET = "smtp_host"
SMTP_PORT_SECRET = "smtp_port"
SMTP_USERNAME_SECRET = "smtp_username"
SMTP_PASSWORD_SECRET = "smtp_password"
SMTP_FROM_EMAIL_SECRET = "smtp_from_email"
SMTP_FROM_NAME_SECRET = "smtp_from_name"
GOOGLE_SERVICE_ACCOUNT_FILE_ENV = "GOOGLE_SERVICE_ACCOUNT_FILE"
PRIMARY_PUBLIC_DOMAIN = "matrikayogaacademy.com"
LEARNER_PASSWORD_MIN_LENGTH = 12
USER_ACCOUNTS_CSV = "user_accounts.csv"
AUTOMATED_REPLY_LOG_CSV = "reply_automation_logs.csv"
PASSWORD_RESET_REQUESTS_CSV = "password_reset_requests.csv"
RAZORPAY_LINKS_CSV = "razorpay_links.csv"
PAGE_WIDGET_KEY = "page_selector"
_ENSURED_WORKSHEETS: set[str] = set()
PASSWORD_RESET_CODE_LENGTH = 4
PASSWORD_RESET_TTL_MINUTES = 60
SUBMISSION_CACHE_TTL_SECONDS = 45
RAZORPAY_KEY_ID_SECRET = "razorpay_key_id"
RAZORPAY_KEY_SECRET_SECRET = "razorpay_key_secret"
RAZORPAY_CURRENCY = "INR"
RAZORPAY_PROVIDER_NAME = "Razorpay"
RAZORPAY_LINK_TTL_HOURS = 24

SUBMISSION_SCHEMAS = {
    "bookings.csv": {
        "worksheet": "bookings",
        "label": "Admissions requests",
        "headers": [
            "submitted_at",
            "page",
            "account_name",
            "account_email",
            "name",
            "email",
            "phone",
            "track",
            "learner_stage",
            "mode",
            "time_period",
            "preferred_time",
            "goals",
            "notes",
        ],
    },
    "attendance.csv": {
        "worksheet": "attendance",
        "label": "Live attendance",
        "headers": [
            "submitted_at",
            "page",
            "account_name",
            "account_email",
            "name",
            "email",
            "session",
            "mode",
            "time_period",
        ],
    },
    "training_applications.csv": {
        "worksheet": "training_applications",
        "label": "Certification applications",
        "headers": [
            "submitted_at",
            "page",
            "account_name",
            "account_email",
            "name",
            "email",
            "time_period",
            "experience",
            "motivation",
        ],
    },
    "kids_enquiries.csv": {
        "worksheet": "kids_enquiries",
        "label": "Kids studio enquiries",
        "headers": [
            "submitted_at",
            "page",
            "account_name",
            "account_email",
            "parent",
            "child",
            "age",
            "email",
            "time_period",
        ],
    },
    "payments.csv": {
        "worksheet": "payments",
        "label": "Payment proofs",
        "headers": [
            "submitted_at",
            "page",
            "account_name",
            "account_email",
            "name",
            "email",
            "time_period",
            "plan",
            "amount",
            "method",
            "provider",
            "payer_handle",
            "reference",
            "notes",
        ],
    },
    "contact_messages.csv": {
        "worksheet": "contact_messages",
        "label": "Contact messages",
        "headers": [
            "submitted_at",
            "page",
            "account_name",
            "account_email",
            "name",
            "email",
            "time_period",
            "message",
        ],
    },
    USER_ACCOUNTS_CSV: {
        "worksheet": "user_accounts",
        "label": "Learner accounts",
        "headers": [
            "created_at",
            "updated_at",
            "full_name",
            "email",
            "phone",
            "linked_payment_app",
            "linked_payment_handle",
            "linked_payment_notes",
            "linked_payment_updated_at",
            "password_hash",
            "password_salt",
            "status",
            "last_login_at",
        ],
    },
    PASSWORD_RESET_REQUESTS_CSV: {
        "worksheet": "password_reset_requests",
        "label": "Password reset requests",
        "headers": [
            "requested_at",
            "request_id",
            "email",
            "code_hash",
            "code_salt",
            "expires_at",
            "status",
            "consumed_at",
            "last_attempt_at",
            "attempt_count",
        ],
    },
    AUTOMATED_REPLY_LOG_CSV: {
        "worksheet": "reply_automation_logs",
        "label": "Automatic reply logs",
        "headers": [
            "sent_at",
            "page",
            "trigger",
            "recipient_name",
            "email",
            "account_email",
            "subject",
            "status",
            "detail",
        ],
    },
    RAZORPAY_LINKS_CSV: {
        "worksheet": "razorpay_links",
        "label": "Razorpay payment links",
        "headers": [
            "created_at",
            "updated_at",
            "page",
            "account_name",
            "account_email",
            "name",
            "email",
            "phone",
            "time_period",
            "plan",
            "amount",
            "currency",
            "provider_hint",
            "reference_id",
            "link_id",
            "status",
            "short_url",
            "callback_url",
            "payment_id",
            "notes",
        ],
    },
}

PAGE_NAMES = [
    "Dashboard",
    "Account",
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
NAV_PAGE_NAMES = [page for page in PAGE_NAMES if page != "Admin"]

TIME_PERIOD_OPTIONS = [
    "Morning",
    "Afternoon",
    "Evening",
    "Weekend",
    "Flexible",
]

PAYMENT_APP_OPTIONS = [
    "Google Pay",
    "PhonePe",
    "Paytm",
    "BHIM",
    "Amazon Pay",
    "Other UPI app",
]
PAYMENT_PROVIDER_OPTIONS = [RAZORPAY_PROVIDER_NAME] + PAYMENT_APP_OPTIONS

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

PUBLIC_RELEASE_CARDS = [
    {
        "kicker": "Public site",
        "title": PUBLIC_SITE_HOST,
        "body": "Share one simple link with families, learners, and teachers so they can reach the academy without confusion.",
        "meta": ["Live now", "Mobile friendly", "Public access"],
    },
    {
        "kicker": "Support rhythm",
        "title": "Friendly follow-through",
        "body": "Each form creates a clear next step, and the team can answer through WhatsApp, email, or class follow-up.",
        "meta": ["Phone", "Email", "WhatsApp"],
    },
    {
        "kicker": "Learning mode",
        "title": "Live + replay structure",
        "body": "The experience works for busy families because it supports both real-time joining and calm catch-up later.",
        "meta": ["Zoom", "Replay path", "IST timing"],
    },
]

OUTCOME_CARDS = [
    {
        "kicker": "Parents",
        "title": "A clear path from enquiry to class",
        "body": "The app keeps admissions, time period choices, and support actions in one calm flow.",
        "meta": ["Less confusion", "Fast action"],
    },
    {
        "kicker": "Children",
        "title": "Playful structure without overload",
        "body": "Kids yoga enquiries feel light, guided, and parent-friendly instead of buried inside long forms.",
        "meta": ["Age-aware", "Easy follow-up"],
    },
    {
        "kicker": "Teachers",
        "title": "A stronger certification journey",
        "body": "Future teachers can move from interest to application with a clearer view of practice, mentorship, and timing.",
        "meta": ["Mentoring", "Cohort-ready"],
    },
]

VISITOR_WELCOME_CARDS = [
    {
        "kicker": "Step 1",
        "title": "Explore the academy calmly",
        "body": "See the main yoga paths, class rhythm, and support style before you commit to anything.",
        "meta": ["No pressure", "Clear layout"],
    },
    {
        "kicker": "Step 2",
        "title": "Create one learner account",
        "body": "Your admissions, payments, attendance, and messages stay connected to the same person and email.",
        "meta": ["Protected access", "Saved profile"],
    },
    {
        "kicker": "Step 3",
        "title": "Move into a guided flow",
        "body": "Book a trial, join live, or submit payment proof with a calmer, more premium experience.",
        "meta": ["One flow", "Follow-up ready"],
    },
]

FAQ_CARDS = [
    {
        "kicker": "FAQ",
        "title": "Can learners join from another city or device?",
        "body": "Yes. The academy runs online, so students can open the public site, join live sessions, and stay connected from anywhere.",
        "meta": ["Online-first", "Any device"],
    },
    {
        "kicker": "FAQ",
        "title": "What happens after a form is submitted?",
        "body": "The request is saved, a confirmation flow is triggered, and the learner is returned home with the next step clearly stated.",
        "meta": ["Saved entries", "Clear next step"],
    },
    {
        "kicker": "FAQ",
        "title": "How does the academy handle timing preferences?",
        "body": "Every form now includes a time period field so the team can recommend the right batch faster.",
        "meta": ["Morning", "Evening", "Weekend"],
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
        "amount_inr": 4200,
        "meta": ["INR 4,200", "4 weeks", "Replay included"],
    },
    {
        "kicker": "Monthly",
        "title": "Trimester Flow",
        "body": "A monthly rhythm for comfort, mobility, and steady practice.",
        "amount_inr": 3500,
        "meta": ["INR 3,500", "Monthly", "Live sessions"],
    },
    {
        "kicker": "Bundle",
        "title": "Prenatal / Postnatal",
        "body": "Eight guided sessions with practical recovery support.",
        "amount_inr": 3200,
        "meta": ["INR 3,200", "8 sessions", "Small batch"],
    },
    {
        "kicker": "Kids",
        "title": "Kids Yoga",
        "body": "Playful classes designed for focus, balance, and calm.",
        "amount_inr": 2800,
        "meta": ["INR 2,800", "Monthly", "Ages 5-14"],
    },
    {
        "kicker": "Professional",
        "title": "Teacher Certification",
        "body": "A full pathway with theory, practicum, and mentored feedback.",
        "amount_inr": 24000,
        "meta": ["INR 24,000", "Certification", "Mentorship"],
    },
]

LEARNING_STYLE_OPTIONS = [
    "Live",
    "Replay",
    "Hybrid",
]

JOURNEY_STATE_KEY = "journey_need"
JOURNEY_TIME_STATE_KEY = "journey_time_period"

JOURNEY_PROFILES = {
    "Pregnancy support": {
        "program_title": "Garbhasanskara Flow",
        "recommended_page": "Admissions",
        "summary": "Begin with a gentle, trimester-aware path that balances breath work, mobility, and calmer emotional support.",
        "next_step": "Best next step: request an admission seat so the academy can match you to a pregnancy-safe batch.",
        "meta": ["Trimester-safe", "Live + replay", "Mentored"],
        "track_keywords": ["Garbhasanskara", "Trimester", "Prenatal"],
        "related_programs": ["Garbhasanskara Flow", "Prenatal + Postnatal Care"],
        "cta_label": "Book this path",
    },
    "Postnatal recovery": {
        "program_title": "Prenatal + Postnatal Care",
        "recommended_page": "Admissions",
        "summary": "Choose the recovery-focused path if you want guided core support, breath steadiness, and a softer return to routine.",
        "next_step": "Best next step: share your current recovery stage in admissions so the team can suggest the gentlest starting point.",
        "meta": ["Healing support", "Small batch", "Flexible timing"],
        "track_keywords": ["Postnatal", "Trimester", "Prenatal"],
        "related_programs": ["Prenatal + Postnatal Care", "Everyday Wellness"],
        "cta_label": "Request recovery guidance",
    },
    "Kids yoga": {
        "program_title": "Kids Yoga Studio",
        "recommended_page": "Kids Studio",
        "summary": "This route keeps movement playful and focused, with child-friendly classes and parent follow-up built into the experience.",
        "next_step": "Best next step: open the kids studio page and send a child enquiry with the preferred time period.",
        "meta": ["Ages 5-14", "Play + calm", "Parent updates"],
        "track_keywords": ["Kids Yoga"],
        "related_programs": ["Kids Yoga Studio"],
        "cta_label": "Open kids studio",
    },
    "Teacher training": {
        "program_title": "Certification Path",
        "recommended_page": "Certification",
        "summary": "Move into the mentored certification journey if you want practice teaching, sequencing, and supervised feedback.",
        "next_step": "Best next step: open certification and share your experience level so the cohort match feels intentional.",
        "meta": ["Certificate", "Mentored", "Practicum"],
        "track_keywords": ["Teacher Certification"],
        "related_programs": ["Certification Path"],
        "cta_label": "Open certification",
    },
    "Everyday wellness": {
        "program_title": "Everyday Wellness",
        "recommended_page": "Admissions",
        "summary": "This is the calmest general entry point for learners who want breathable structure without needing a specialty track first.",
        "next_step": "Best next step: request a trial so the academy can place you in a simple morning, evening, or weekend rhythm.",
        "meta": ["Beginners", "Weekend friendly", "Replay access"],
        "track_keywords": ["Prenatal Practice", "Postnatal Recovery", "Garbhasanskara"],
        "related_programs": ["Everyday Wellness", "Garbhasanskara Flow"],
        "cta_label": "Book a trial",
    },
}

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

PAGE_SPIRIT_PANELS = {
    "Dashboard": {
        "eyebrow": "Landing energy",
        "title": "Step into a quieter yoga rhythm.",
        "body": "The public academy experience is now built to feel softer, greener, and easier to trust on a first visit.",
        "symbol": "✿",
        "mantra": "Arrive · breathe · continue",
    },
    "Account": {
        "eyebrow": "Sacred access",
        "title": "One calm identity for your entire journey.",
        "body": "Your learner account now anchors admissions, attendance, payments, and support inside one protected flow.",
        "symbol": "ॐ",
        "mantra": "Sign in · settle · move forward",
    },
    "Programs": {
        "eyebrow": "Paths",
        "title": "Different journeys, one grounded philosophy.",
        "body": "Each program is shaped around breath, rhythm, and stage-aware support rather than pressure or overload.",
        "symbol": "☼",
        "mantra": "Practice · support · growth",
    },
    "Schedule": {
        "eyebrow": "Rhythm",
        "title": "A timetable that feels like breath, not noise.",
        "body": "Morning, evening, and specialty sessions now sit inside a calmer visual rhythm for easier planning.",
        "symbol": "☾",
        "mantra": "Morning · evening · weekend",
    },
    "Admissions": {
        "eyebrow": "Welcome",
        "title": "Begin your admission with clarity and ease.",
        "body": "The academy team now receives a more complete view of each learner without asking for long back-and-forth details.",
        "symbol": "❋",
        "mantra": "Share · match · begin",
    },
    "Live Studio": {
        "eyebrow": "Practice",
        "title": "Live practice now feels more ceremonial and focused.",
        "body": "Attendance, replay support, and live links are framed as one joined class experience instead of separate chores.",
        "symbol": "✺",
        "mantra": "Join · practice · reflect",
    },
    "Certification": {
        "eyebrow": "Teacher path",
        "title": "A mentored path with steadier spiritual tone.",
        "body": "The certification flow now carries more of the academy’s yoga identity from first interest to final practicum.",
        "symbol": "✶",
        "mantra": "Learn · teach · deepen",
    },
    "Kids Studio": {
        "eyebrow": "Joyful movement",
        "title": "Playful yoga can still feel beautifully guided.",
        "body": "The kids section now balances warmth, focus, and parent clarity with a more intentional visual language.",
        "symbol": "✸",
        "mantra": "Play · breathe · rest",
    },
    "Payments": {
        "eyebrow": "Exchange",
        "title": "Payments now sit inside the same calm learner journey.",
        "body": "Families can link a preferred third-party payment app and carry that context straight into proof submission.",
        "symbol": "✺",
        "mantra": "Choose · pay · confirm",
    },
    "Contact": {
        "eyebrow": "Reach out",
        "title": "Support should feel held, not lost.",
        "body": "Messages, timing preferences, and replies now sit inside a softer communication experience built for trust.",
        "symbol": "♡",
        "mantra": "Ask · receive · continue",
    },
    "Admin": {
        "eyebrow": "Stewardship",
        "title": "The academy control room stays calm too.",
        "body": "Even the admin layer now carries the same grounded visual language while keeping team access protected.",
        "symbol": "✿",
        "mantra": "Review · respond · protect",
    },
}

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


def normalize_payment_handle(value: str) -> str:
    return normalize_text(value)


def valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


def valid_phone(value: str) -> bool:
    digits = digits_only(value)
    if not digits:
        return False
    return len(digits) == 10 or (digits.startswith("91") and len(digits) == 12)


def valid_password(value: str) -> bool:
    return len(str(value)) >= LEARNER_PASSWORD_MIN_LENGTH


def password_hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()


def new_password_credentials(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    return password_hash(password, salt), salt


def password_matches(password: str, stored_hash: str, stored_salt: str) -> bool:
    if not stored_hash or not stored_salt:
        return False
    return hmac.compare_digest(password_hash(password, stored_salt), stored_hash)


def verification_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(PASSWORD_RESET_CODE_LENGTH))


def build_whatsapp_url(message: str) -> str:
    return f"https://wa.me/{digits_only(normalize_phone(CONTACT_PHONE))}?text={quote(message)}"


def build_mailto_url(subject: str, body: str) -> str:
    return f"mailto:{CONTACT_EMAIL}?subject={quote(subject)}&body={quote(body)}"


def payment_app_link(
    app_name: str,
    learner: Mapping[str, object] | None = None,
    *,
    amount_inr: int | float | None = None,
    note: str = "",
) -> str:
    learner = learner or {}
    learner_name = normalize_text(str(learner.get("full_name", "")) or "Matrika learner")
    payment_note = normalize_text(note) or f"{app_name} payment for {learner_name}"
    link = f"{PAYMENT_UPI_URL}&tn={quote(payment_note)}"
    if amount_inr not in (None, "", 0):
        try:
            amount = float(amount_inr)
        except (TypeError, ValueError):
            amount = 0
        if amount > 0:
            link = f"{link}&am={amount:.2f}"
    return link


def payment_plan_by_title(title: str) -> dict[str, object]:
    for item in PAYMENT_PLANS:
        if str(item.get("title", "")) == str(title):
            return dict(item)
    return {}


def payment_plan_amount(title: str) -> int:
    plan = payment_plan_by_title(title)
    amount = plan.get("amount_inr", 0)
    try:
        return max(int(amount), 0)
    except (TypeError, ValueError):
        return 0


def razorpay_configured() -> bool:
    return bool(str(get_secret_value(RAZORPAY_KEY_ID_SECRET, "")).strip()) and bool(
        str(get_secret_value(RAZORPAY_KEY_SECRET_SECRET, "")).strip()
    )


def razorpay_mode() -> str:
    key_id = str(get_secret_value(RAZORPAY_KEY_ID_SECRET, "")).strip().lower()
    if key_id.startswith("rzp_live_"):
        return "live"
    if key_id.startswith("rzp_test_"):
        return "test"
    return "unknown"


def razorpay_amount_subunits(amount_inr: int | float) -> int:
    try:
        return max(int(round(float(amount_inr) * 100)), 0)
    except (TypeError, ValueError):
        return 0


def razorpay_reference_id(plan: str, email: str) -> str:
    plan_token = re.sub(r"[^a-z0-9]+", "", str(plan).lower())[:8] or "plan"
    user_token = re.sub(r"[^a-z0-9]+", "", normalize_email(email).split("@")[0])[:8] or "learner"
    unique_token = secrets.token_hex(2)
    return f"ma-{plan_token}-{user_token}-{unique_token}"[:40]


def razorpay_callback_url() -> str:
    return PUBLIC_SITE_URL


@st.cache_data(show_spinner=False)
def qr_code_png_bytes(data: str) -> bytes | None:
    clean_data = str(data).strip()
    if not clean_data:
        return None
    try:
        import qrcode
    except ImportError:
        return None

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(clean_data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#33512f", back_color="#f5f8ef")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def render_payment_qr(
    title: str,
    data: str,
    caption: str,
    *,
    meta: list[str] | tuple[str, ...] | None = None,
) -> None:
    qr_bytes = qr_code_png_bytes(data)
    render_card(
        title,
        caption,
        kicker="Scan to pay",
        meta=list(meta or ["QR ready", "Mobile friendly"]),
        class_name="info-card",
    )
    if qr_bytes:
        st.image(qr_bytes, use_container_width=True)
    else:
        st.caption("QR generation becomes available once the QR package is installed on the host.")
        st.code(data)


def razorpay_notes_payload(
    *,
    plan: str,
    time_period: str,
    account_email: str,
    provider_hint: str,
) -> dict[str, str]:
    def trimmed(value: object) -> str:
        return normalize_text(str(value))[:250]

    return {
        "plan": trimmed(plan),
        "time_period": trimmed(time_period),
        "account_email": trimmed(account_email),
        "provider_hint": trimmed(provider_hint),
    }


def razorpay_request(method: str, endpoint: str, payload: Mapping[str, object] | None = None) -> tuple[bool, dict[str, object] | None, str]:
    key_id = str(get_secret_value(RAZORPAY_KEY_ID_SECRET, "")).strip()
    key_secret = str(get_secret_value(RAZORPAY_KEY_SECRET_SECRET, "")).strip()
    if not key_id or not key_secret:
        return False, None, "Razorpay is not configured yet."

    request_headers = {
        "Authorization": "Basic "
        + base64.b64encode(f"{key_id}:{key_secret}".encode("utf-8")).decode("utf-8"),
        "Accept": "application/json",
    }
    body = None
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")

    request = Request(
        f"{RAZORPAY_API_BASE_URL}{endpoint}",
        data=body,
        headers=request_headers,
        method=method.upper(),
    )
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {}
        error_block = data.get("error", {}) if isinstance(data, Mapping) else {}
        detail = ""
        if isinstance(error_block, Mapping):
            detail = str(error_block.get("description") or error_block.get("reason") or "").strip()
        message = detail or raw or f"Razorpay request failed with status {exc.code}."
        return False, data if isinstance(data, dict) else None, message
    except URLError as exc:
        return False, None, f"Razorpay could not be reached: {exc.reason}"
    except Exception as exc:
        return False, None, f"Razorpay request could not be completed: {exc}"

    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return False, None, "Razorpay returned an unreadable response."
    if not isinstance(data, dict):
        return False, None, "Razorpay returned an unexpected response."
    return True, data, ""


def create_razorpay_payment_link(
    *,
    learner: Mapping[str, object],
    name: str,
    email: str,
    phone: str,
    plan: str,
    time_period: str,
    amount_inr: int,
    provider_hint: str,
    notes: str,
) -> tuple[bool, dict[str, str] | None, str]:
    clean_name = normalize_text(name)
    clean_email = normalize_email(email)
    clean_phone = digits_only(phone)
    clean_notes = normalize_text(notes)
    amount = razorpay_amount_subunits(amount_inr)
    if amount <= 0:
        return False, None, "Enter a valid payment amount before creating the Razorpay link."

    reference_id = razorpay_reference_id(plan, clean_email)
    customer = {
        "name": clean_name,
        "email": clean_email,
    }
    if clean_phone:
        customer["contact"] = clean_phone

    payload = {
        "amount": amount,
        "currency": RAZORPAY_CURRENCY,
        "description": f"{plan} · {time_period} · Matrika Academy",
        "reference_id": reference_id,
        "customer": customer,
        "reminder_enable": True,
        "callback_url": razorpay_callback_url(),
        "callback_method": "get",
        "notes": razorpay_notes_payload(
            plan=plan,
            time_period=time_period,
            account_email=clean_email,
            provider_hint=provider_hint,
        ),
    }
    if clean_notes:
        payload["notes"]["academy_note"] = clean_notes[:250]

    ok, response, detail = razorpay_request("POST", "/v1/payment_links", payload)
    if not ok or not response:
        return False, None, detail or "Razorpay could not create the payment link."

    row = {
        "created_at": current_timestamp(),
        "updated_at": current_timestamp(),
        "page": "Payments",
        "account_name": str(learner.get("full_name", "")).strip(),
        "account_email": str(learner.get("email", "")).strip(),
        "name": clean_name,
        "email": clean_email,
        "phone": normalize_phone(clean_phone),
        "time_period": time_period,
        "plan": plan,
        "amount": str(amount_inr),
        "currency": str(response.get("currency") or RAZORPAY_CURRENCY),
        "provider_hint": provider_hint,
        "reference_id": str(response.get("reference_id") or reference_id),
        "link_id": str(response.get("id", "")),
        "status": str(response.get("status", "created")),
        "short_url": str(response.get("short_url", "")),
        "callback_url": razorpay_callback_url(),
        "payment_id": "",
        "notes": clean_notes,
    }
    upsert_submission_row(RAZORPAY_LINKS_CSV, row, ("link_id", "reference_id"))
    return True, row, ""


def fetch_razorpay_payment_link(link_id: str) -> tuple[bool, dict[str, object] | None, str]:
    clean_link_id = normalize_text(link_id)
    if not clean_link_id:
        return False, None, "A Razorpay link id is required to refresh status."
    return razorpay_request("GET", f"/v1/payment_links/{quote(clean_link_id)}")


def first_razorpay_payment_id(response: Mapping[str, object]) -> str:
    payments = response.get("payments", [])
    if not isinstance(payments, list) or not payments:
        return ""
    first = payments[0]
    if not isinstance(first, Mapping):
        return ""
    return str(first.get("payment_id") or first.get("id") or "").strip()


def upsert_submission_row(csv_name: str, row: dict[str, object], key_fields: tuple[str, ...]) -> None:
    rows = load_submission_rows(csv_name)
    normalized_row = {str(key): str(value) for key, value in row.items()}
    updated = False
    for existing in rows:
        if any(normalized_row.get(key, "") and str(existing.get(key, "")) == normalized_row.get(key, "") for key in key_fields):
            existing.update(normalized_row)
            updated = True
            break
    if not updated:
        rows.append(normalized_row)
    replace_rows(csv_name, rows)


def latest_razorpay_link(email: str) -> dict[str, str] | None:
    target = normalize_email(email)
    for row in reversed(load_submission_rows(RAZORPAY_LINKS_CSV)):
        if normalize_email(row.get("account_email", "") or row.get("email", "")) == target:
            return row
    return None


def refresh_razorpay_link_status(link_row: Mapping[str, object]) -> tuple[bool, dict[str, str] | None, str]:
    link_id = str(link_row.get("link_id", "")).strip()
    ok, response, detail = fetch_razorpay_payment_link(link_id)
    if not ok or not response:
        return False, None, detail or "Razorpay status could not be refreshed."

    updated_row = {
        "created_at": str(link_row.get("created_at", current_timestamp())),
        "updated_at": current_timestamp(),
        "page": str(link_row.get("page", "Payments")),
        "account_name": str(link_row.get("account_name", "")),
        "account_email": str(link_row.get("account_email", "")),
        "name": str(link_row.get("name", "")),
        "email": str(link_row.get("email", "")),
        "phone": str(link_row.get("phone", "")),
        "time_period": str(link_row.get("time_period", "")),
        "plan": str(link_row.get("plan", "")),
        "amount": str(link_row.get("amount", "")),
        "currency": str(response.get("currency") or link_row.get("currency", RAZORPAY_CURRENCY)),
        "provider_hint": str(link_row.get("provider_hint", "")),
        "reference_id": str(response.get("reference_id") or link_row.get("reference_id", "")),
        "link_id": str(response.get("id") or link_id),
        "status": str(response.get("status") or link_row.get("status", "")),
        "short_url": str(response.get("short_url") or link_row.get("short_url", "")),
        "callback_url": str(response.get("callback_url") or link_row.get("callback_url", razorpay_callback_url())),
        "payment_id": first_razorpay_payment_id(response) or str(link_row.get("payment_id", "")),
        "notes": str(link_row.get("notes", "")),
    }
    upsert_submission_row(RAZORPAY_LINKS_CSV, updated_row, ("link_id", "reference_id"))
    return True, updated_row, ""


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
    return bool(get_google_service_account_secret()) and bool(get_secret_value(GOOGLE_SHEET_ID_SECRET))


def env_name_for(secret_key: str) -> str:
    return secret_key.upper()


def get_streamlit_secret(secret_key: str) -> object:
    try:
        return st.secrets.get(secret_key, None)
    except StreamlitSecretNotFoundError:
        return None


def get_secret_value(secret_key: str, default: object = "") -> object:
    streamlit_value = get_streamlit_secret(secret_key)
    if isinstance(streamlit_value, Mapping):
        return dict(streamlit_value)
    if streamlit_value not in (None, ""):
        return streamlit_value
    return os.getenv(env_name_for(secret_key), default)


def get_google_service_account_secret() -> object:
    streamlit_value = get_streamlit_secret(GOOGLE_SERVICE_ACCOUNT_SECRET)
    if isinstance(streamlit_value, Mapping):
        return dict(streamlit_value)
    if streamlit_value not in (None, ""):
        return streamlit_value

    env_value = os.getenv(env_name_for(GOOGLE_SERVICE_ACCOUNT_SECRET), "").strip()
    if env_value:
        return env_value

    file_path = os.getenv(GOOGLE_SERVICE_ACCOUNT_FILE_ENV, "").strip()
    if file_path:
        path = Path(file_path)
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def current_timestamp() -> str:
    return datetime.now(IST_ZONE).strftime("%Y-%m-%d %H:%M:%S IST")


def current_time() -> datetime:
    return datetime.now(IST_ZONE)


def format_timestamp(moment: datetime) -> str:
    return moment.astimezone(IST_ZONE).strftime("%Y-%m-%d %H:%M:%S IST")


def log_runtime_issue(message: str) -> None:
    text = normalize_text(message)
    if not text:
        return
    try:
        notices = list(st.session_state.get("runtime_issues", []))
        notices.append({"at": current_timestamp(), "message": text})
        st.session_state.runtime_issues = notices[-20:]
    except Exception:
        pass
    print(text)


def parse_timestamp(value: str) -> datetime | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S IST")
    except ValueError:
        return None
    return parsed.replace(tzinfo=IST_ZONE)


def smtp_configured() -> bool:
    required = [
        SMTP_HOST_SECRET,
        SMTP_PORT_SECRET,
        SMTP_USERNAME_SECRET,
        SMTP_PASSWORD_SECRET,
    ]
    return all(str(get_secret_value(key, "")).strip() for key in required)


def smtp_port() -> int:
    try:
        return int(get_secret_value(SMTP_PORT_SECRET, 587))
    except (TypeError, ValueError):
        return 587


def smtp_from_email() -> str:
    value = str(get_secret_value(SMTP_FROM_EMAIL_SECRET, "")).strip()
    return value or str(get_secret_value(SMTP_USERNAME_SECRET, "")).strip() or CONTACT_EMAIL


def smtp_from_name() -> str:
    value = str(get_secret_value(SMTP_FROM_NAME_SECRET, "")).strip()
    return value or "Matrika Academy"


def smtp_password() -> str:
    password = str(get_secret_value(SMTP_PASSWORD_SECRET, "")).strip()
    host = str(get_secret_value(SMTP_HOST_SECRET, "")).strip().lower()
    if "gmail.com" in host:
        return password.replace(" ", "")
    return password


def send_confirmation_email(
    *,
    to_email: str,
    recipient_name: str,
    subject: str,
    submission_title: str,
    details: list[tuple[str, object]],
    next_steps: str,
    intro_text: str | None = None,
) -> tuple[bool, str]:
    if not smtp_configured():
        return False, "Email confirmations are not configured yet."

    detail_lines = [f"- {label}: {value}" for label, value in details if str(value).strip()]
    body_lines = [
        f"Hi {recipient_name or 'there'},",
        "",
        intro_text or f"We have received your {submission_title} submission at Matrika Academy.",
        "",
        "Details:",
        *detail_lines,
        "",
        next_steps,
        "",
        f"Support email: {CONTACT_EMAIL}",
        f"Support phone: {CONTACT_PHONE}",
        "",
        "Matrika Academy",
    ]

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{smtp_from_name()} <{smtp_from_email()}>"
    message["To"] = to_email
    message["Reply-To"] = CONTACT_EMAIL
    message.set_content("\n".join(body_lines))

    host = str(get_secret_value(SMTP_HOST_SECRET, "")).strip()
    username = str(get_secret_value(SMTP_USERNAME_SECRET, "")).strip()
    password = smtp_password()
    port = smtp_port()

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=20) as server:
                server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                server.login(username, password)
                server.send_message(message)
    except Exception as exc:
        return False, f"Confirmation email could not be sent: {exc}"

    return True, f"Confirmation email sent to {to_email}."


def render_confirmation_result(result: tuple[bool, str]) -> None:
    delivered, message = result
    if delivered:
        st.info(message)
    elif "not configured yet" in message:
        st.caption("Confirmation emails will start once SMTP secrets are added.")
    else:
        log_runtime_issue(message)
        st.caption("Email delivery is temporarily unavailable. Your request is still saved in the academy.")


def send_automatic_reply(
    *,
    trigger: str,
    page: str,
    to_email: str,
    recipient_name: str,
    subject: str,
    submission_title: str,
    details: list[tuple[str, object]],
    next_steps: str,
    account_email: str = "",
    intro_text: str | None = None,
) -> tuple[bool, str]:
    result = send_confirmation_email(
        to_email=to_email,
        recipient_name=recipient_name,
        subject=subject,
        submission_title=submission_title,
        details=details,
        next_steps=next_steps,
        intro_text=intro_text,
    )
    delivered, detail = result
    status = "sent" if delivered else ("pending_configuration" if "not configured yet" in detail else "failed")
    save_row(
        AUTOMATED_REPLY_LOG_CSV,
        {
            "sent_at": current_timestamp(),
            "page": page,
            "trigger": trigger,
            "recipient_name": recipient_name,
            "email": to_email,
            "account_email": account_email or to_email,
            "subject": subject,
            "status": status,
            "detail": detail,
        },
    )
    return result


def worksheet_name_for(csv_name: str) -> str:
    schema = SUBMISSION_SCHEMAS.get(csv_name)
    if schema:
        return str(schema["worksheet"])
    return Path(csv_name).stem


def worksheet_headers_for(csv_name: str, row: dict | None = None) -> list[str]:
    schema = SUBMISSION_SCHEMAS.get(csv_name)
    if schema:
        return list(schema["headers"])
    if row:
        return list(row.keys())
    return []


def get_google_spreadsheet():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return None

    raw_secret = get_google_service_account_secret()
    sheet_id = get_secret_value(GOOGLE_SHEET_ID_SECRET, "")
    if not raw_secret or not sheet_id:
        return None

    if isinstance(raw_secret, Mapping):
        service_account_info = dict(raw_secret)
    else:
        service_account_info = parse_service_account_secret(str(raw_secret))

    return get_google_spreadsheet_cached(json.dumps(service_account_info, sort_keys=True), str(sheet_id))


@st.cache_resource(show_spinner=False)
def get_google_spreadsheet_cached(service_account_json: str, sheet_id: str):
    import gspread
    from google.oauth2.service_account import Credentials

    credentials = Credentials.from_service_account_info(
        json.loads(service_account_json),
        scopes=list(GOOGLE_SHEETS_SCOPE),
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(sheet_id)


def parse_service_account_secret(raw_secret: str) -> dict:
    try:
        return json.loads(raw_secret)
    except json.JSONDecodeError:
        pass

    # Streamlit multiline strings can turn the private key's escaped newlines
    # into literal newlines. Re-escape just that field and try JSON again.
    fixed_secret = re.sub(
        r'("private_key"\s*:\s*")(.*?)(",\s*"client_email")',
        lambda match: (
            match.group(1)
            + match.group(2).replace("\\", "\\\\").replace("\n", "\\n")
            + match.group(3)
        ),
        raw_secret,
        flags=re.DOTALL,
    )
    return json.loads(fixed_secret)


def ensure_google_worksheet(csv_name: str, row: dict | None = None):
    spreadsheet = get_google_spreadsheet()
    if spreadsheet is None:
        return None

    headers = worksheet_headers_for(csv_name, row)
    worksheet_name = worksheet_name_for(csv_name)
    import gspread

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=max(1000, len(headers) + 10),
            cols=max(20, len(headers) + 2),
        )

    if headers and worksheet_name not in _ENSURED_WORKSHEETS:
        current_headers = worksheet.row_values(1)
        if current_headers != headers:
            existing_values = worksheet.get_all_values()
            migrated_values = [headers]
            if current_headers and existing_values:
                for row_values in existing_values[1:]:
                    old_row = {
                        current_headers[index]: row_values[index] if index < len(row_values) else ""
                        for index in range(len(current_headers))
                    }
                    migrated_values.append([old_row.get(header, "") for header in headers])
            worksheet.clear()
            worksheet.update("A1", migrated_values, value_input_option="RAW")
    _ENSURED_WORKSHEETS.add(worksheet_name)
    return worksheet


def ensure_google_submission_sheets() -> None:
    if not google_persistence_enabled():
        return

    try:
        spreadsheet = get_google_spreadsheet()
        if spreadsheet is None:
            return

        for csv_name in SUBMISSION_SCHEMAS:
            ensure_google_worksheet(csv_name)

        update_google_overview_sheet(spreadsheet)
    except Exception:
        return


def update_google_overview_sheet(spreadsheet=None) -> None:
    if spreadsheet is None:
        spreadsheet = get_google_spreadsheet()
    if spreadsheet is None:
        return

    overview = get_overview_worksheet(spreadsheet)
    if overview is None:
        return

    overview_rows = [
        ["worksheet", "stores", "saved_rows", "latest_submission"],
    ]
    for csv_name, config in SUBMISSION_SCHEMAS.items():
        worksheet = spreadsheet.worksheet(str(config["worksheet"]))
        values = worksheet.get_all_values()
        data_rows = values[1:] if values else []
        latest_submission = data_rows[-1][0] if data_rows and data_rows[-1] else ""
        overview_rows.append(
            [
                str(config["worksheet"]),
                str(config["label"]),
                str(len(data_rows)),
                latest_submission,
            ]
        )
    current_values = overview.get_all_values()
    if current_values != overview_rows:
        overview.clear()
        overview.update("A1", overview_rows, value_input_option="RAW")


def update_google_overview_row(csv_name: str, latest_submission: str, spreadsheet=None, worksheet=None) -> None:
    if spreadsheet is None:
        spreadsheet = get_google_spreadsheet()
    if spreadsheet is None:
        return

    overview = get_overview_worksheet(spreadsheet)
    if overview is None:
        return

    schema_items = list(SUBMISSION_SCHEMAS.items())
    row_index = next(
        (index + 2 for index, (name, _) in enumerate(schema_items) if name == csv_name),
        None,
    )
    if row_index is None:
        return

    config = SUBMISSION_SCHEMAS[csv_name]
    if worksheet is None:
        worksheet = spreadsheet.worksheet(str(config["worksheet"]))
    saved_rows = max(len(worksheet.col_values(1)) - 1, 0)
    overview.update(
        f"A{row_index}:D{row_index}",
        [[str(config["worksheet"]), str(config["label"]), str(saved_rows), latest_submission]],
        value_input_option="RAW",
    )


def get_overview_worksheet(spreadsheet):
    import gspread

    try:
        return spreadsheet.worksheet(OVERVIEW_WORKSHEET)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(
            title=OVERVIEW_WORKSHEET,
            rows=max(20, len(SUBMISSION_SCHEMAS) + 5),
            cols=6,
        )


def append_row_to_google_sheet(csv_name: str, row: dict) -> bool:
    if not google_persistence_enabled():
        return False

    worksheet = ensure_google_worksheet(csv_name, row)
    if worksheet is None:
        return False

    headers = worksheet_headers_for(csv_name, row)
    if not headers:
        headers = list(row.keys())
    worksheet.append_row([str(row.get(key, "")) for key in headers], value_input_option="RAW")
    return True


def admin_password_configured() -> bool:
    return bool(str(get_secret_value(ADMIN_PASSWORD_SECRET, "")).strip())


def admin_authenticated() -> bool:
    return bool(st.session_state.get("admin_authenticated", False))


def list_submission_sources() -> list[str]:
    names = {path.name for path in DATA_DIR.glob("*.csv")}
    if google_persistence_enabled():
        names.update(SUBMISSION_SCHEMAS.keys())
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
    try:
        spreadsheet = get_google_spreadsheet()
        if spreadsheet is None:
            return []

        import gspread

        worksheet_name = worksheet_name_for(csv_name)
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            return []
        values = worksheet.get_all_records()
    except Exception:
        return []
    return [{str(key): str(value) for key, value in row.items()} for row in values]


def write_local_rows(csv_name: str, rows: list[dict[str, object]]) -> None:
    file_path = DATA_DIR / csv_name
    headers = worksheet_headers_for(csv_name, rows[0] if rows else None)
    if not headers and rows:
        headers = list(rows[0].keys())
    with file_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


def local_rows_signature(csv_name: str) -> str:
    file_path = DATA_DIR / csv_name
    if not file_path.exists():
        return "missing"
    stat = file_path.stat()
    return f"{stat.st_mtime_ns}:{stat.st_size}"


@st.cache_data(show_spinner=False, ttl=SUBMISSION_CACHE_TTL_SECONDS)
def load_submission_rows_cached(csv_name: str, signature: str, google_enabled: bool) -> list[dict[str, str]]:
    del signature

    local_rows = read_local_rows(csv_name)
    if local_rows:
        return local_rows

    if google_enabled:
        google_rows = read_google_rows(csv_name)
        if google_rows:
            write_local_rows(csv_name, google_rows)
            return google_rows
    return []


def load_submission_rows(csv_name: str) -> list[dict[str, str]]:
    return load_submission_rows_cached(
        csv_name,
        local_rows_signature(csv_name),
        google_persistence_enabled(),
    )


def storage_status_lines() -> list[str]:
    lines = []
    if google_persistence_enabled():
        lines.append("Google Sheets persistence is active.")
    else:
        lines.append("Google Sheets persistence is not configured yet.")
        lines.append(
            f"Add `{GOOGLE_SHEET_ID_SECRET}` and `{GOOGLE_SERVICE_ACCOUNT_SECRET}` in Streamlit secrets or host env vars."
        )
    if admin_password_configured():
        lines.append("Admin password is configured.")
    else:
        lines.append(f"Add `{ADMIN_PASSWORD_SECRET}` in Streamlit secrets or host env vars to protect the admin page.")
    if smtp_configured():
        lines.append("Automatic reply emails and password reset verification are configured.")
    else:
        lines.append(
            f"Add `{SMTP_HOST_SECRET}`, `{SMTP_PORT_SECRET}`, `{SMTP_USERNAME_SECRET}`, and `{SMTP_PASSWORD_SECRET}` in secrets or env vars to send automatic replies and password reset codes."
        )
    if razorpay_configured():
        lines.append("Razorpay payment links are configured.")
    else:
        lines.append(
            f"Add `{RAZORPAY_KEY_ID_SECRET}` and `{RAZORPAY_KEY_SECRET_SECRET}` in secrets or env vars to generate Razorpay payment links."
        )
    lines.append("Learner accounts are stored with hashed passwords.")
    return lines


def google_sheet_url() -> str | None:
    sheet_id = str(get_secret_value(GOOGLE_SHEET_ID_SECRET, "")).strip()
    if not sheet_id:
        return None
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}"


def rows_to_csv_bytes(rows: list[dict[str, str]]) -> bytes:
    if not rows:
        return b""

    buffer = io.StringIO()
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def save_row(csv_name: str, row: dict) -> None:
    file_path = DATA_DIR / csv_name
    headers = worksheet_headers_for(csv_name, row)
    if not headers:
        headers = list(row.keys())
    wrote_local_row = False

    existing_rows: list[dict[str, str]] = []
    if file_path.exists():
        with file_path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            current_headers = reader.fieldnames or []
            existing_rows = list(reader)
        if current_headers != headers:
            with file_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=headers)
                writer.writeheader()
                for existing_row in existing_rows:
                    writer.writerow({key: existing_row.get(key, "") for key in headers})
                writer.writerow({key: row.get(key, "") for key in headers})
            wrote_local_row = True

    if not wrote_local_row:
        with file_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            if not file_path.exists() or file_path.stat().st_size == 0:
                writer.writeheader()
            writer.writerow({key: row.get(key, "") for key in headers})

    if google_persistence_enabled():
        try:
            append_row_to_google_sheet(csv_name, row)
        except Exception as exc:
            log_runtime_issue(f"Google Sheets sync failed for {csv_name}: {exc}")


def replace_rows(csv_name: str, rows: list[dict[str, object]]) -> None:
    headers = worksheet_headers_for(csv_name, rows[0] if rows else None)
    if not headers and rows:
        headers = list(rows[0].keys())
    write_local_rows(csv_name, rows)

    if not google_persistence_enabled():
        return

    try:
        spreadsheet = get_google_spreadsheet()
        worksheet = ensure_google_worksheet(
            csv_name,
            rows[0] if rows else {header: "" for header in headers},
        )
        if spreadsheet is None or worksheet is None:
            return
        worksheet.clear()
        values = [headers]
        values.extend([[str(row.get(key, "")) for key in headers] for row in rows])
        worksheet.update("A1", values, value_input_option="RAW")
        update_google_overview_sheet(spreadsheet)
    except Exception as exc:
        log_runtime_issue(f"Google Sheets sync failed for {csv_name}: {exc}")


def learner_authenticated() -> bool:
    return bool(st.session_state.get("learner_authenticated", False))


def current_learner_profile() -> dict[str, str]:
    return {
        "full_name": str(st.session_state.get("learner_name", "")).strip(),
        "email": str(st.session_state.get("learner_email", "")).strip(),
        "phone": str(st.session_state.get("learner_phone", "")).strip(),
        "linked_payment_app": str(st.session_state.get("learner_payment_app", "")).strip(),
        "linked_payment_handle": str(st.session_state.get("learner_payment_handle", "")).strip(),
        "linked_payment_notes": str(st.session_state.get("learner_payment_notes", "")).strip(),
    }


def sync_learner_session(account: Mapping[str, object]) -> None:
    st.session_state.learner_authenticated = True
    st.session_state.learner_name = str(account.get("full_name", "")).strip()
    st.session_state.learner_email = normalize_email(str(account.get("email", "")))
    st.session_state.learner_phone = normalize_phone(str(account.get("phone", "")))
    st.session_state.learner_payment_app = str(account.get("linked_payment_app", "")).strip()
    st.session_state.learner_payment_handle = normalize_payment_handle(str(account.get("linked_payment_handle", "")))
    st.session_state.learner_payment_notes = str(account.get("linked_payment_notes", "")).strip()
    st.session_state.latest_razorpay_link = latest_razorpay_link(str(account.get("email", ""))) or {}


def logout_learner() -> None:
    st.session_state.learner_authenticated = False
    st.session_state.learner_name = ""
    st.session_state.learner_email = ""
    st.session_state.learner_phone = ""
    st.session_state.learner_payment_app = ""
    st.session_state.learner_payment_handle = ""
    st.session_state.learner_payment_notes = ""
    st.session_state.latest_razorpay_link = {}


def remember_recent_account_creation(email: str) -> None:
    st.session_state.recent_account_creation = {
        "email": normalize_email(email),
        "timestamp": time.time(),
    }


def recent_account_creation_matches(email: str) -> bool:
    recent = st.session_state.get("recent_account_creation", {})
    recent_email = normalize_email(str(recent.get("email", "")))
    recent_timestamp = float(recent.get("timestamp", 0) or 0)
    return bool(recent_email) and recent_email == normalize_email(email) and (time.time() - recent_timestamp) < SUBMISSION_COOLDOWN_SECONDS


def load_user_accounts() -> list[dict[str, str]]:
    return load_submission_rows(USER_ACCOUNTS_CSV)


def find_user_account(email: str) -> dict[str, str] | None:
    target = normalize_email(email)
    for row in reversed(load_user_accounts()):
        if normalize_email(row.get("email", "")) == target and str(row.get("status", "active")).lower() == "active":
            return row
    return None


def create_user_account(full_name: str, email: str, phone: str, password: str) -> dict[str, str]:
    current_accounts = load_user_accounts()
    hashed_password, salt = new_password_credentials(password)
    now = current_timestamp()
    row = {
        "created_at": now,
        "updated_at": now,
        "full_name": normalize_text(full_name),
        "email": normalize_email(email),
        "phone": normalize_phone(phone),
        "linked_payment_app": "",
        "linked_payment_handle": "",
        "linked_payment_notes": "",
        "linked_payment_updated_at": "",
        "password_hash": hashed_password,
        "password_salt": salt,
        "status": "active",
        "last_login_at": now,
    }
    current_accounts.append(row)
    replace_rows(USER_ACCOUNTS_CSV, current_accounts)
    return row


def record_user_login(email: str) -> dict[str, str] | None:
    current_accounts = load_user_accounts()
    target = normalize_email(email)
    updated_row = None
    for row in current_accounts:
        if normalize_email(row.get("email", "")) == target:
            row["updated_at"] = current_timestamp()
            row["last_login_at"] = current_timestamp()
            updated_row = {str(key): str(value) for key, value in row.items()}
            break
    if updated_row is None:
        return None
    replace_rows(USER_ACCOUNTS_CSV, current_accounts)
    return updated_row


def update_user_account(email: str, updates: Mapping[str, object]) -> dict[str, str] | None:
    current_accounts = load_user_accounts()
    target = normalize_email(email)
    updated_row = None
    for row in current_accounts:
        if normalize_email(row.get("email", "")) == target:
            for key, value in updates.items():
                row[str(key)] = str(value)
            row["updated_at"] = current_timestamp()
            updated_row = {str(key): str(value) for key, value in row.items()}
            break
    if updated_row is None:
        return None
    replace_rows(USER_ACCOUNTS_CSV, current_accounts)
    return updated_row


def load_password_reset_requests() -> list[dict[str, str]]:
    return load_submission_rows(PASSWORD_RESET_REQUESTS_CSV)


def update_password_reset_requests(rows: list[dict[str, object]]) -> None:
    replace_rows(PASSWORD_RESET_REQUESTS_CSV, rows)


def expire_password_reset_requests(email: str = "") -> None:
    target = normalize_email(email)
    current_requests = load_password_reset_requests()
    changed = False
    now = current_time()
    for row in current_requests:
        if target and normalize_email(row.get("email", "")) != target:
            continue
        if str(row.get("status", "")).lower() == "pending":
            expires_at = parse_timestamp(str(row.get("expires_at", "")))
            if expires_at and expires_at <= now:
                row["status"] = "expired"
                changed = True
    if changed:
        update_password_reset_requests(current_requests)


def create_password_reset_request(email: str) -> tuple[str, dict[str, str]]:
    target = normalize_email(email)
    current_requests = load_password_reset_requests()
    now = current_time()
    changed = False
    for row in current_requests:
        if normalize_email(row.get("email", "")) == target and str(row.get("status", "")).lower() == "pending":
            row["status"] = "superseded"
            changed = True

    code = verification_code()
    code_hash_value, code_salt = new_password_credentials(code)
    request_row = {
        "requested_at": format_timestamp(now),
        "request_id": secrets.token_hex(8),
        "email": target,
        "code_hash": code_hash_value,
        "code_salt": code_salt,
        "expires_at": format_timestamp(now + timedelta(minutes=PASSWORD_RESET_TTL_MINUTES)),
        "status": "pending",
        "consumed_at": "",
        "last_attempt_at": "",
        "attempt_count": "0",
    }
    current_requests.append(request_row)
    if changed or current_requests:
        update_password_reset_requests(current_requests)
    return code, {str(key): str(value) for key, value in request_row.items()}


def latest_active_password_reset_request(email: str) -> dict[str, str] | None:
    expire_password_reset_requests(email)
    target = normalize_email(email)
    for row in reversed(load_password_reset_requests()):
        if normalize_email(row.get("email", "")) != target:
            continue
        if str(row.get("status", "")).lower() != "pending":
            continue
        expires_at = parse_timestamp(str(row.get("expires_at", "")))
        if expires_at and expires_at > current_time():
            return row
    return None


def record_password_reset_attempt(email: str, request_id: str) -> None:
    target = normalize_email(email)
    current_requests = load_password_reset_requests()
    changed = False
    for row in current_requests:
        if normalize_email(row.get("email", "")) != target or str(row.get("request_id", "")) != str(request_id):
            continue
        attempts = int(str(row.get("attempt_count", "0") or "0"))
        row["attempt_count"] = str(attempts + 1)
        row["last_attempt_at"] = current_timestamp()
        changed = True
        break
    if changed:
        update_password_reset_requests(current_requests)


def consume_password_reset_request(email: str, request_id: str, status: str = "used") -> None:
    target = normalize_email(email)
    current_requests = load_password_reset_requests()
    changed = False
    for row in current_requests:
        if normalize_email(row.get("email", "")) != target or str(row.get("request_id", "")) != str(request_id):
            continue
        row["status"] = status
        row["consumed_at"] = current_timestamp()
        changed = True
        break
    if changed:
        update_password_reset_requests(current_requests)


def verify_password_reset_code(email: str, code: str) -> tuple[bool, str, dict[str, str] | None]:
    target = normalize_email(email)
    request_row = latest_active_password_reset_request(target)
    if not request_row:
        return False, "No active password reset request was found for this email. Request a new verification code.", None
    request_id = str(request_row.get("request_id", ""))
    record_password_reset_attempt(target, request_id)
    if not password_matches(code, str(request_row.get("code_hash", "")), str(request_row.get("code_salt", ""))):
        return False, "The verification code is incorrect. Check the email and try again.", None
    return True, "Verification code accepted.", request_row


def reset_user_password(email: str, new_password: str, request_row: Mapping[str, object]) -> dict[str, str] | None:
    hashed_password, salt = new_password_credentials(new_password)
    updated_account = update_user_account(
        email,
        {
            "password_hash": hashed_password,
            "password_salt": salt,
            "last_login_at": current_timestamp(),
        },
    )
    if updated_account:
        consume_password_reset_request(email, str(request_row.get("request_id", "")))
    return updated_account


def preferred_payment_app(learner: Mapping[str, object]) -> str:
    return str(learner.get("linked_payment_app", "")).strip()


def preferred_payment_handle(learner: Mapping[str, object]) -> str:
    return normalize_payment_handle(str(learner.get("linked_payment_handle", "")))


def authenticate_user_account(email: str, password: str) -> dict[str, str] | None:
    account = find_user_account(email)
    if not account:
        return None
    if not password_matches(password, str(account.get("password_hash", "")), str(account.get("password_salt", ""))):
        return None
    return record_user_login(email) or account


def require_learner_account(page_name: str, description: str) -> bool:
    if learner_authenticated():
        return True

    render_card(
        "Create or log into your learner account",
        description,
        kicker="Account required",
        meta=["Sign up once", "Automatic replies", "Protected access"],
        class_name="info-card",
    )
    action_cols = st.columns(2)
    with action_cols[0]:
        st.button(
            "Open learner account",
            key=f"gate_{page_name}_account",
            use_container_width=True,
            on_click=jump_to,
            args=("Account",),
        )
    with action_cols[1]:
        st.link_button(
            "Need help first?",
            build_whatsapp_url(
                f"Hi Matrika Academy, I want help creating my learner account before I use the {page_name.lower()} section."
            ),
            use_container_width=True,
        )
    return False


def sanitize_rows_for_admin(csv_name: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if csv_name == USER_ACCOUNTS_CSV:
        sanitized: list[dict[str, str]] = []
        for row in rows:
            clean_row = dict(row)
            if clean_row.get("password_hash"):
                clean_row["password_hash"] = "hidden"
            if clean_row.get("password_salt"):
                clean_row["password_salt"] = "hidden"
            sanitized.append(clean_row)
        return sanitized

    if csv_name == PASSWORD_RESET_REQUESTS_CSV:
        sanitized = []
        for row in rows:
            clean_row = dict(row)
            if clean_row.get("code_hash"):
                clean_row["code_hash"] = "hidden"
            if clean_row.get("code_salt"):
                clean_row["code_salt"] = "hidden"
            sanitized.append(clean_row)
        return sanitized

    return rows


def jump_to(page: str) -> None:
    st.session_state.page = page


def open_page_with_journey(page: str, need: str = "", time_period: str = "Flexible") -> None:
    if need:
        st.session_state[JOURNEY_STATE_KEY] = need
    if time_period:
        st.session_state[JOURNEY_TIME_STATE_KEY] = time_period
    jump_to(page)


def sync_page_from_navigation() -> None:
    selected_page = str(st.session_state.get(PAGE_WIDGET_KEY, PAGE_NAMES[0])).strip()
    if selected_page in PAGE_NAMES:
        st.session_state.page = selected_page


@st.cache_data(show_spinner=False)
def asset_data_uri(asset_path: str) -> str:
    path = Path(asset_path)
    if not path.exists():
        return ""

    suffix = path.suffix.lower()
    mime_type = "image/svg+xml" if suffix == ".svg" else "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def logo_data_uri() -> str:
    return asset_data_uri(str(LOGO_PATH))


def buddha_background_data_uri() -> str:
    return asset_data_uri(str(BUDDHA_BACKGROUND_PATH))


def submission_signature(csv_name: str, row: dict) -> str:
    comparable_row = {key: value for key, value in row.items() if key != "submitted_at"}
    return json.dumps({"csv_name": csv_name, "row": comparable_row}, sort_keys=True, default=str)


def duplicate_submission_detected(csv_name: str, row: dict) -> bool:
    now = time.time()
    recent = {
        str(signature): float(timestamp)
        for signature, timestamp in st.session_state.get("recent_submissions", {}).items()
        if now - float(timestamp) < SUBMISSION_COOLDOWN_SECONDS
    }
    signature = submission_signature(csv_name, row)
    if signature in recent:
        st.session_state.recent_submissions = recent
        return True

    recent[signature] = now
    st.session_state.recent_submissions = recent
    return False


def confirmation_flash_detail(result: tuple[bool, str] | None) -> str:
    if not result:
        return ""

    delivered, message = result
    if delivered:
        return message
    if "not configured yet" in message:
        return "Confirmation emails will start once SMTP secrets are added."
    log_runtime_issue(message)
    return "Email delivery is temporarily unavailable right now, but your academy request was still saved."


def queue_flash_notice(kind: str, title: str, body: str, detail: str = "") -> None:
    st.session_state.flash_notice = {
        "kind": kind,
        "title": title,
        "body": body,
        "detail": detail,
    }


def render_page_loader(title: str = "Returning home", body: str = "Hold on while we refresh the academy home page.") -> None:
    st.markdown(
        f"""
        <div class="page-loader-overlay">
            <div class="page-loader-card">
                <div class="page-loader-spinner"></div>
                <div class="page-loader-title">{esc(title)}</div>
                <div class="page-loader-copy">{esc(body)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def send_user_home(
    *,
    kind: str,
    title: str,
    body: str,
    email_result: tuple[bool, str] | None = None,
) -> None:
    queue_flash_notice(kind, title, body, confirmation_flash_detail(email_result))
    render_page_loader()
    time.sleep(0.7)
    jump_to("Dashboard")
    st.rerun()


def chips(items: list[str] | tuple[str, ...]) -> str:
    return "".join(f"<span class='meta-chip'>{esc(item)}</span>" for item in items)


def journey_need_options() -> list[str]:
    return list(JOURNEY_PROFILES.keys())


def journey_profile(need: str) -> dict[str, object]:
    profile = JOURNEY_PROFILES.get(need)
    if profile:
        return dict(profile)
    fallback_need = journey_need_options()[0]
    return dict(JOURNEY_PROFILES[fallback_need])


def program_card_by_title(title: str) -> dict[str, object]:
    for card in PROGRAM_CARDS:
        if str(card.get("title", "")) == str(title):
            return dict(card)
    return {}


def related_program_cards(need: str) -> list[dict[str, object]]:
    profile = journey_profile(need)
    titles = list(profile.get("related_programs", []))
    cards = [program_card_by_title(title) for title in titles]
    return [card for card in cards if card]


def session_time_period(row: Mapping[str, object]) -> str:
    day = str(row.get("Day", "")).strip().lower()
    if day in {"sat", "sun"}:
        return "Weekend"

    time_text = str(row.get("Time", "")).strip().upper()
    match = re.fullmatch(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_text)
    if not match:
        return "Flexible"

    hour = int(match.group(1)) % 12
    if match.group(3) == "PM":
        hour += 12
    if hour < 12:
        return "Morning"
    if hour < 17:
        return "Afternoon"
    return "Evening"


def schedule_rows_for_need(
    need: str | None = None,
    *,
    time_period: str = "Flexible",
    track: str = "",
) -> list[dict[str, str]]:
    profile = journey_profile(need) if need else {}
    keywords = [str(item).lower() for item in profile.get("track_keywords", [])]
    selected_track = str(track).strip()
    selected_period = str(time_period).strip() or "Flexible"
    rows: list[dict[str, str]] = []

    for row in WEEKLY_SCHEDULE:
        row_copy = {str(key): str(value) for key, value in row.items()}
        row_copy["Time period"] = session_time_period(row_copy)

        if selected_period not in {"", "All periods", "Flexible"} and row_copy["Time period"] != selected_period:
            continue
        if selected_track and selected_track != "All tracks" and row_copy.get("Track") != selected_track:
            continue
        if keywords and not any(keyword in row_copy.get("Track", "").lower() for keyword in keywords):
            continue

        rows.append(row_copy)

    return rows


def schedule_card_items(rows: list[dict[str, str]], *, limit: int = 3) -> list[dict[str, object]]:
    return [
        {
            "kicker": row.get("Day", "Session"),
            "title": f'{row.get("Time", "")} · {row.get("Track", "")}',
            "body": row.get("Focus", ""),
            "meta": [row.get("Time period", ""), "IST"],
        }
        for row in rows[:limit]
    ]


def mode_support_copy(mode: str) -> str:
    if mode == "Replay":
        return "Replay-first learners can still use these live slots as anchor points and catch up later without stress."
    if mode == "Hybrid":
        return "Hybrid works well here because the learner can join live when possible and rely on replays on busier weeks."
    return "This path suits learners who want to show up for the live rhythm and stay close to the class energy each week."


def render_interactive_pathfinder(
    section_key: str,
    *,
    eyebrow: str,
    title: str,
    body: str,
    show_schedule_preview: bool = True,
    show_related_programs: bool = False,
) -> None:
    render_section(eyebrow, title, body)
    needs = journey_need_options()
    stored_need = str(st.session_state.get(JOURNEY_STATE_KEY, needs[0]))
    stored_time_period = str(st.session_state.get(JOURNEY_TIME_STATE_KEY, "Flexible"))
    need_index = needs.index(stored_need) if stored_need in needs else 0
    time_index = TIME_PERIOD_OPTIONS.index(stored_time_period) if stored_time_period in TIME_PERIOD_OPTIONS else len(TIME_PERIOD_OPTIONS) - 1

    left, right = st.columns([0.95, 1.05])
    with left:
        selected_need = st.radio(
            "Who is this path for?",
            needs,
            index=need_index,
            key=f"{section_key}_journey_need",
        )
        selected_time_period = st.selectbox(
            "Best time period",
            TIME_PERIOD_OPTIONS,
            index=time_index,
            key=f"{section_key}_journey_time_period",
        )
        selected_mode = st.select_slider(
            "Learning style",
            options=LEARNING_STYLE_OPTIONS,
            value="Hybrid",
            key=f"{section_key}_journey_mode",
        )

    st.session_state[JOURNEY_STATE_KEY] = selected_need
    st.session_state[JOURNEY_TIME_STATE_KEY] = selected_time_period

    profile = journey_profile(selected_need)
    matching_rows = schedule_rows_for_need(selected_need, time_period=selected_time_period)

    with right:
        render_card(
            str(profile.get("program_title", "")),
            str(profile.get("summary", "")),
            kicker="Recommended path",
            meta=[
                selected_time_period,
                selected_mode,
                *list(profile.get("meta", []))[:2],
            ],
            class_name="feature-card",
        )
        st.caption(str(profile.get("next_step", "")))
        st.info(mode_support_copy(selected_mode))
        cta_cols = st.columns(2)
        with cta_cols[0]:
            st.button(
                str(profile.get("cta_label", "Open next step")),
                key=f"{section_key}_path_cta",
                use_container_width=True,
                on_click=open_page_with_journey,
                args=(str(profile.get("recommended_page", "Programs")), selected_need, selected_time_period),
            )
        with cta_cols[1]:
            st.button(
                "See matching classes",
                key=f"{section_key}_schedule_cta",
                use_container_width=True,
                on_click=open_page_with_journey,
                args=("Schedule", selected_need, selected_time_period),
            )

    if show_schedule_preview:
        if matching_rows:
            render_card_grid(
                schedule_card_items(matching_rows, limit=min(3, len(matching_rows))),
                columns=min(3, len(matching_rows)),
                class_name="schedule-card",
            )
        else:
            st.info(
                "No current live slot exactly matches that combination yet. Keep the same journey and try Flexible, or message the academy for a custom batch."
            )

    if show_related_programs:
        cards = related_program_cards(selected_need)
        if cards:
            render_card_grid(cards, columns=min(3, len(cards)))


def render_program_comparison() -> None:
    render_section(
        "Compare two paths",
        "Put two academy journeys next to each other before you decide.",
        "This makes it easier for families and first-time learners to compare the tone and outcome of each path without scrolling back and forth.",
    )
    options = [str(card.get("title", "")) for card in PROGRAM_CARDS]
    left, right = st.columns(2)
    default_right_index = 1 if len(options) > 1 else 0
    with left:
        left_program = st.selectbox("Program one", options, index=0, key="program_compare_left")
    with right:
        right_program = st.selectbox("Program two", options, index=default_right_index, key="program_compare_right")

    compare_cols = st.columns(2)
    for slot, selected_program in zip(compare_cols, [left_program, right_program]):
        card = program_card_by_title(selected_program)
        if not card:
            continue
        with slot:
            render_card(
                str(card.get("title", "")),
                str(card.get("body", "")),
                kicker=str(card.get("kicker", "")),
                meta=list(card.get("meta", [])),
                class_name="timeline-card",
            )

def apply_theme() -> None:
    buddha_background = buddha_background_data_uri()
    css = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #f5f8ef;
            --bg-soft: #e4eed9;
            --bg-deep: #d6e6bf;
            --ink: #203629;
            --muted: #617767;
            --pista: #a7c97a;
            --pista-deep: #7fa956;
            --forest: #4c6d3f;
            --moss: #33512f;
            --lotus: #fbfff5;
            --mist: #edf5e4;
            --line: rgba(76, 109, 63, 0.16);
            --card: rgba(252, 255, 247, 0.8);
            --shadow: 0 18px 45px rgba(60, 92, 47, 0.13);
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
            position: relative;
            isolation: isolate;
            background:
                radial-gradient(circle at 10% 16%, rgba(167, 201, 122, 0.22), transparent 24%),
                radial-gradient(circle at 84% 10%, rgba(127, 169, 86, 0.18), transparent 20%),
                radial-gradient(circle at 50% 100%, rgba(214, 230, 191, 0.45), transparent 28%),
                linear-gradient(180deg, var(--bg) 0%, var(--bg-soft) 56%, #f2f7ea 100%);
        }

        .stApp::before {
            content: "";
            position: fixed;
            right: clamp(1rem, 3vw, 2.5rem);
            bottom: clamp(0.75rem, 3.5vw, 2rem);
            width: min(38vw, 430px);
            height: min(60vw, 520px);
            BUDDHA_BG_LAYER
            background-position: center bottom;
            background-repeat: no-repeat;
            background-size: contain;
            opacity: 0.2;
            pointer-events: none;
            z-index: 0;
            filter: drop-shadow(0 20px 34px rgba(76, 109, 63, 0.12));
        }

        [data-testid="stSidebar"],
        [data-testid="stAppViewContainer"],
        [data-testid="stHeader"] {
            position: relative;
            z-index: 1;
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
                linear-gradient(180deg, rgba(248, 253, 241, 0.97), rgba(232, 241, 217, 0.95));
            border-right: 1px solid var(--line);
            backdrop-filter: blur(12px);
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
            border-radius: 26px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(10px);
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
            border-radius: 20px;
            object-fit: cover;
            box-shadow: 0 12px 26px rgba(76, 109, 63, 0.18);
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

        .brand-fallback {
            width: 64px;
            height: 64px;
            display: grid;
            place-items: center;
            border-radius: 20px;
            background: linear-gradient(135deg, var(--pista), var(--forest));
            color: white;
            font-family: "Cormorant Garamond", serif;
            font-size: 2rem;
            font-weight: 700;
            box-shadow: 0 12px 26px rgba(76, 109, 63, 0.18);
        }

        .topbar-shell {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 0.9rem 1.1rem;
            padding: 1rem 1.15rem;
            margin-bottom: 1rem;
            border-radius: 30px;
            border: 1px solid var(--line);
            background: linear-gradient(135deg, rgba(251, 255, 245, 0.9), rgba(232, 241, 217, 0.86));
            box-shadow: var(--shadow);
            backdrop-filter: blur(12px);
            animation: matrika-fade-up 0.55s ease both;
        }

        .topbar-brand {
            display: inline-flex;
            align-items: center;
            gap: 0.95rem;
            text-decoration: none;
            color: var(--ink) !important;
        }

        .topbar-brand:hover {
            color: var(--ink) !important;
        }

        .topbar-logo {
            width: 58px;
            height: 58px;
            border-radius: 18px;
            object-fit: cover;
            box-shadow: 0 12px 24px rgba(76, 109, 63, 0.16);
        }

        .brand-lockup {
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }

        .brand-label {
            font-family: "Cormorant Garamond", serif;
            font-size: 2rem;
            line-height: 0.9;
        }

        .brand-subtitle {
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.4;
        }

        .topbar-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
        }

        .topbar-chip {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 2.5rem;
            padding: 0.55rem 0.9rem;
            border-radius: 999px;
            border: 1px solid rgba(76, 109, 63, 0.18);
            background: rgba(251, 255, 245, 0.92);
            color: var(--ink) !important;
            text-decoration: none;
            font-weight: 800;
            box-shadow: 0 10px 20px rgba(76, 109, 63, 0.08);
        }

        .topbar-chip:hover {
            color: var(--ink) !important;
            transform: translateY(-1px);
        }

        .site-chip {
            background: linear-gradient(135deg, rgba(214, 230, 191, 0.92), rgba(167, 201, 122, 0.36)) !important;
            border-color: rgba(127, 169, 86, 0.3) !important;
        }

        .flash-banner {
            margin-bottom: 1rem;
            padding: 1rem 1.1rem;
            border-radius: 24px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
            animation: matrika-fade-up 0.5s ease both;
        }

        .flash-banner h3 {
            margin: 0 0 0.35rem;
            font-size: 1.4rem;
        }

        .flash-banner p {
            margin: 0;
            line-height: 1.6;
        }

        .flash-banner-detail {
            margin-top: 0.55rem;
            color: var(--muted);
            font-size: 0.92rem;
        }

        .flash-banner-success {
            background: linear-gradient(135deg, rgba(251, 255, 245, 0.96), rgba(230, 241, 213, 0.96));
        }

        .flash-banner-info {
            background: linear-gradient(135deg, rgba(251, 255, 245, 0.95), rgba(238, 246, 229, 0.95));
        }

        .flash-banner-warning {
            background: linear-gradient(135deg, rgba(255, 252, 246, 0.96), rgba(233, 241, 214, 0.96));
        }

        .page-loader-overlay {
            position: fixed;
            inset: 0;
            z-index: 1000000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
            background: rgba(245, 248, 239, 0.62);
            backdrop-filter: blur(6px);
        }

        .page-loader-card {
            min-width: min(92vw, 360px);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.9rem;
            text-align: center;
            padding: 1.25rem 1.4rem;
            border-radius: 28px;
            border: 1px solid var(--line);
            background: rgba(252, 255, 247, 0.96);
            box-shadow: 0 24px 60px rgba(60, 92, 47, 0.18);
        }

        .page-loader-spinner {
            width: 60px;
            height: 60px;
            border-radius: 999px;
            border: 5px solid rgba(167, 201, 122, 0.2);
            border-top-color: var(--pista-deep);
            border-right-color: var(--forest);
            animation: matrika-spin 0.9s linear infinite;
        }

        .page-loader-title {
            font-family: "Cormorant Garamond", serif;
            font-size: 1.9rem;
            line-height: 0.95;
        }

        .page-loader-copy {
            color: var(--muted);
            font-size: 0.96rem;
            line-height: 1.55;
        }

        @keyframes matrika-spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 999px;
            background: rgba(167, 201, 122, 0.18);
            color: var(--forest);
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            padding: 0.38rem 0.7rem;
        }

        .hero-card {
            position: relative;
            overflow: hidden;
            padding: clamp(1.5rem, 3vw, 2.4rem);
            background:
                linear-gradient(145deg, rgba(251, 255, 245, 0.92), rgba(229, 239, 213, 0.8));
            animation: matrika-fade-up 0.65s ease both;
        }

        .hero-card::before {
            content: "";
            position: absolute;
            right: -1.5rem;
            bottom: -1rem;
            width: min(38vw, 280px);
            height: min(48vw, 340px);
            BUDDHA_BG_LAYER
            background-position: center bottom;
            background-repeat: no-repeat;
            background-size: contain;
            opacity: 0.16;
            pointer-events: none;
        }

        .hero-card::after {
            content: "";
            position: absolute;
            inset: auto -12% -28% auto;
            width: 320px;
            height: 320px;
            border-radius: 50%;
            background: radial-gradient(
                circle,
                rgba(167, 201, 122, 0.28) 0%,
                rgba(167, 201, 122, 0.08) 52%,
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
            font-size: 1.04rem;
            line-height: 1.72;
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
            background: rgba(251, 255, 245, 0.88);
            border: 1px solid rgba(76, 109, 63, 0.16);
            color: var(--forest);
            font-weight: 700;
            font-size: 0.86rem;
            padding: 0.42rem 0.76rem;
        }

        .page-intro {
            padding: 1.15rem 1.2rem 1.1rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, rgba(251, 255, 245, 0.9), rgba(230, 241, 214, 0.82));
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

        .section-heading-top {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.55rem 0.85rem;
            margin-bottom: 0.25rem;
        }

        .section-icons {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            color: var(--forest);
            font-size: 0.92rem;
            letter-spacing: 0.04em;
            opacity: 0.8;
        }

        .kicker-symbol {
            display: inline-flex;
            margin-right: 0.28rem;
            opacity: 0.85;
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
            animation: matrika-fade-up 0.62s ease both;
            transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
        }

        .feature-card:hover,
        .info-card:hover,
        .schedule-card:hover,
        .pricing-card:hover,
        .timeline-card:hover,
        .contact-card:hover,
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 22px 42px rgba(76, 109, 63, 0.16);
            border-color: rgba(127, 169, 86, 0.28);
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
            background: linear-gradient(180deg, var(--pista-deep), var(--forest));
        }

        .card-kicker {
            color: var(--forest);
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
            background: rgba(167, 201, 122, 0.18);
            color: var(--forest);
            padding: 0.36rem 0.64rem;
            font-size: 0.78rem;
            font-weight: 700;
        }

        .metric-card {
            padding: 1rem;
            background: linear-gradient(180deg, rgba(251, 255, 245, 0.86), rgba(237, 245, 228, 0.82));
            transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
            animation: matrika-fade-up 0.72s ease both;
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
            background: rgba(251, 255, 245, 0.76);
            border: 1px solid var(--line);
            box-shadow: 0 10px 24px rgba(76, 109, 63, 0.08);
        }

        .timeline-index {
            width: 2.15rem;
            height: 2.15rem;
            border-radius: 999px;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, var(--pista), var(--forest));
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
            border: 1px solid rgba(127, 169, 86, 0.26);
            background: linear-gradient(135deg, rgba(251, 255, 245, 0.9), rgba(236, 245, 227, 0.84));
            padding: 1rem 1.1rem;
            box-shadow: 0 14px 28px rgba(76, 109, 63, 0.08);
        }

        .illustration-panel {
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: minmax(0, 1.2fr) minmax(220px, 0.8fr);
            gap: 1rem;
            align-items: center;
            padding: 1.2rem 1.2rem 1.1rem;
            margin: 1rem 0 1.2rem;
            border-radius: 28px;
            border: 1px solid rgba(127, 169, 86, 0.24);
            background: linear-gradient(135deg, rgba(251, 255, 245, 0.94), rgba(232, 241, 217, 0.78));
            box-shadow: 0 18px 38px rgba(76, 109, 63, 0.1);
            animation: matrika-fade-up 0.58s ease both;
        }

        .illustration-panel::after {
            content: "";
            position: absolute;
            inset: auto -8% -30% auto;
            width: 240px;
            height: 240px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(167, 201, 122, 0.24), rgba(167, 201, 122, 0) 70%);
            pointer-events: none;
        }

        .illustration-copy {
            position: relative;
            z-index: 1;
        }

        .illustration-copy h3 {
            margin: 0.52rem 0 0.3rem;
            font-size: clamp(1.85rem, 4vw, 2.7rem);
            line-height: 0.96;
        }

        .illustration-copy p {
            margin: 0;
            color: var(--muted);
            line-height: 1.68;
            max-width: 60ch;
        }

        .illustration-art {
            position: relative;
            min-height: 220px;
            display: grid;
            place-items: center;
        }

        .illustration-orbit {
            position: absolute;
            inset: 18% 14%;
            border-radius: 999px;
            border: 1px solid rgba(127, 169, 86, 0.22);
            animation: matrika-float 7s ease-in-out infinite;
        }

        .illustration-orbit::before,
        .illustration-orbit::after {
            content: "";
            position: absolute;
            inset: 12%;
            border-radius: 999px;
            border: 1px dashed rgba(127, 169, 86, 0.18);
        }

        .illustration-orbit::after {
            inset: 24%;
        }

        .illustration-symbol {
            position: relative;
            z-index: 1;
            width: 7.5rem;
            height: 7.5rem;
            display: grid;
            place-items: center;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(167, 201, 122, 0.94), rgba(76, 109, 63, 0.94));
            color: white;
            font-size: 3rem;
            box-shadow: 0 16px 34px rgba(76, 109, 63, 0.18);
        }

        .illustration-symbol::before {
            content: "";
            position: absolute;
            inset: -1.15rem;
            border-radius: 999px;
            border: 1px solid rgba(127, 169, 86, 0.22);
        }

        .illustration-mantra {
            position: absolute;
            bottom: 0.1rem;
            left: 50%;
            transform: translateX(-50%);
            padding: 0.42rem 0.78rem;
            border-radius: 999px;
            background: rgba(251, 255, 245, 0.9);
            border: 1px solid rgba(127, 169, 86, 0.2);
            color: var(--forest);
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            white-space: nowrap;
            z-index: 1;
        }

        .form-banner {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 0.9rem;
            align-items: start;
            padding: 1rem 1.05rem;
            margin-bottom: 0.85rem;
            border-radius: 22px;
            border: 1px solid rgba(127, 169, 86, 0.22);
            background: linear-gradient(135deg, rgba(251, 255, 245, 0.92), rgba(234, 243, 220, 0.86));
            box-shadow: 0 12px 26px rgba(76, 109, 63, 0.08);
            animation: matrika-fade-up 0.5s ease both;
        }

        .form-badge {
            width: 2.55rem;
            height: 2.55rem;
            display: grid;
            place-items: center;
            border-radius: 999px;
            background: linear-gradient(135deg, var(--pista), var(--forest));
            color: white;
            font-size: 1.05rem;
            box-shadow: 0 10px 20px rgba(76, 109, 63, 0.16);
        }

        .form-banner h3 {
            margin: 0;
            font-size: 1.35rem;
            line-height: 1;
        }

        .form-banner p {
            margin: 0.28rem 0 0;
            color: var(--muted);
            line-height: 1.6;
        }

        .footer-shell {
            margin-top: 2rem;
            padding: 1rem 1.15rem;
            border-radius: 24px;
            border: 1px solid var(--line);
            background: rgba(251, 255, 245, 0.84);
            box-shadow: var(--shadow);
        }

        .footer-shell p {
            margin: 0.2rem 0 0;
            color: var(--muted);
            line-height: 1.6;
        }

        .stButton > button {
            border-radius: 999px;
            border: 1px solid transparent;
            background: linear-gradient(135deg, var(--pista), var(--forest));
            color: white;
            font-weight: 800;
            padding: 0.68rem 1rem;
            box-shadow: 0 12px 24px rgba(127, 169, 86, 0.26);
            transition: transform 0.18s ease, filter 0.18s ease, box-shadow 0.18s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            filter: brightness(0.98);
            box-shadow: 0 14px 28px rgba(76, 109, 63, 0.24);
        }

        [data-testid="stLinkButton"] a {
            border-radius: 999px !important;
            border: 1px solid rgba(76, 109, 63, 0.16) !important;
            background: rgba(251, 255, 245, 0.86) !important;
            color: var(--ink) !important;
            font-weight: 800 !important;
            box-shadow: 0 10px 20px rgba(76, 109, 63, 0.08) !important;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="select"] > div,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input {
            border-radius: 18px !important;
            border: 1px solid rgba(76, 109, 63, 0.18) !important;
            background: rgba(251, 255, 245, 0.94) !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
            color: var(--ink) !important;
        }

        textarea,
        input {
            color: var(--ink) !important;
        }

        label,
        .stSelectbox label,
        .stTextInput label,
        .stTextArea label,
        .stNumberInput label {
            color: var(--forest) !important;
            font-weight: 700 !important;
        }

        div[data-testid="stForm"] {
            position: relative;
            overflow: hidden;
            padding: 1.05rem 1rem 0.35rem;
            border-radius: 28px;
            border: 1px solid rgba(127, 169, 86, 0.24);
            background: linear-gradient(145deg, rgba(251, 255, 245, 0.95), rgba(234, 243, 220, 0.8));
            box-shadow: 0 18px 36px rgba(76, 109, 63, 0.1);
            margin-bottom: 0.4rem;
            animation: matrika-fade-up 0.62s ease both;
        }

        div[data-testid="stForm"]::before {
            content: "";
            position: absolute;
            right: -1rem;
            bottom: -1rem;
            width: 180px;
            height: 220px;
            BUDDHA_BG_LAYER
            background-position: center bottom;
            background-repeat: no-repeat;
            background-size: contain;
            opacity: 0.08;
            pointer-events: none;
        }

        div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button,
        div[data-testid="stForm"] .stButton > button {
            margin-top: 0.4rem;
        }

        div[data-testid="stForm"] .stCaptionContainer,
        div[data-testid="stForm"] .stMarkdown {
            position: relative;
            z-index: 1;
        }

        div[data-testid="stSpinner"],
        .stSpinner {
            position: fixed;
            inset: 0;
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(245, 248, 239, 0.5);
            backdrop-filter: blur(4px);
        }

        div[data-testid="stSpinner"] > div,
        .stSpinner > div {
            padding: 1rem 1.15rem;
            border-radius: 22px;
            background: rgba(251, 255, 245, 0.94);
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
        }

        hr {
            border-color: rgba(76, 109, 63, 0.12);
        }

        @keyframes matrika-fade-up {
            from {
                opacity: 0;
                transform: translateY(14px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes matrika-float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
        }

        @media (max-width: 980px) {
            .hero-title {
                max-width: none;
            }

            .stApp::before {
                width: min(48vw, 300px);
                height: min(70vw, 380px);
                opacity: 0.11;
            }

            .illustration-panel {
                grid-template-columns: 1fr;
            }

            .illustration-art {
                min-height: 180px;
            }
        }

        @media (max-width: 760px) {
            .topbar-shell {
                padding: 0.9rem 0.95rem;
            }

            .brand-label {
                font-size: 1.75rem;
            }

            .brand-subtitle {
                font-size: 0.86rem;
            }

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

            .illustration-symbol {
                width: 6rem;
                height: 6rem;
                font-size: 2.45rem;
            }

            .illustration-mantra {
                position: static;
                transform: none;
                margin-top: 0.85rem;
            }

            .hero-card::before {
                width: min(46vw, 210px);
                height: min(60vw, 260px);
                right: -1.25rem;
                bottom: -0.75rem;
                opacity: 0.12;
            }

            .stApp::before {
                right: -1rem;
                bottom: 4rem;
                width: min(64vw, 280px);
                height: min(80vw, 340px);
                opacity: 0.12;
            }
        }
        </style>
        """
    if buddha_background:
        css = css.replace("BUDDHA_BG_LAYER", f'background-image: url("{buddha_background}");')
    else:
        css = css.replace("BUDDHA_BG_LAYER", "background-image: none;")
    st.markdown(css, unsafe_allow_html=True)


def render_card(
    title: str,
    body: str,
    *,
    kicker: str | None = None,
    meta: list[str] | tuple[str, ...] | None = None,
    class_name: str = "feature-card",
) -> None:
    kicker_html = (
        f"<div class='card-kicker'><span class='kicker-symbol' aria-hidden='true'>&#10047;</span>{esc(kicker)}</div>"
        if kicker
        else ""
    )
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
            <div class="section-heading-top">
                <span class="eyebrow">{esc(eyebrow)}</span>
                <div class="section-icons" aria-hidden="true">
                    <span>&#10047;</span>
                    <span>&#2384;</span>
                    <span>&#10047;</span>
                </div>
            </div>
            <h2>{esc(title)}</h2>
            <p>{esc(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_form_banner(symbol: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="form-banner">
            <div class="form-badge" aria-hidden="true">{symbol}</div>
            <div>
                <h3>{esc(title)}</h3>
                <p>{esc(body)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_illustration_panel(page_name: str) -> None:
    panel = PAGE_SPIRIT_PANELS.get(page_name)
    if not panel:
        return

    st.markdown(
        f"""
        <div class="illustration-panel">
            <div class="illustration-copy">
                <span class="eyebrow">{esc(panel["eyebrow"])}</span>
                <h3>{esc(panel["title"])}</h3>
                <p>{esc(panel["body"])}</p>
            </div>
            <div class="illustration-art" aria-hidden="true">
                <div class="illustration-orbit"></div>
                <div class="illustration-symbol">{panel["symbol"]}</div>
                <div class="illustration-mantra">{esc(panel["mantra"])}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        f"""
        <div class="footer-shell">
            <span class="eyebrow">Public release</span>
            <h3 style="margin:0.55rem 0 0.2rem;">Matrika Academy is live and share-ready.</h3>
            <p>
                Public site: <strong>{esc(PUBLIC_SITE_HOST)}</strong><br/>
                Support: {esc(CONTACT_EMAIL)} · {esc(CONTACT_PHONE)}<br/>
                Classes are structured for live joining, replay follow-up, and calm navigation on desktop or mobile.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_flash_notice() -> None:
    notice = st.session_state.pop("flash_notice", None)
    if not notice:
        return

    detail_html = (
        f"<div class='flash-banner-detail'>{esc(notice.get('detail', ''))}</div>"
        if notice.get("detail")
        else ""
    )
    kind = str(notice.get("kind", "success")).lower()
    st.markdown(
        f"""
        <div class="flash-banner flash-banner-{esc(kind)}">
            <h3>{esc(notice.get("title", ""))}</h3>
            <p>{esc(notice.get("body", ""))}</p>
            {detail_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    logo_src = logo_data_uri()
    if logo_src:
        logo_markup = f"<img src='{logo_src}' alt='Matrika Academy logo' class='topbar-logo' />"
    else:
        logo_markup = "<div class='brand-fallback topbar-logo'>M</div>"

    st.markdown(
        f"""
        <div class="topbar-shell">
            <a class="topbar-brand" href="{HOME_HREF}" target="_self">
                {logo_markup}
                <div class="brand-lockup">
                    <span class="brand-label">Matrika Academy</span>
                    <span class="brand-subtitle">Tap the logo anytime to return home and restart the journey calmly.</span>
                </div>
            </a>
            <div class="topbar-actions">
                <a class="topbar-chip" href="{HOME_HREF}" target="_self">Home</a>
                <a class="topbar-chip site-chip" href="{esc(PUBLIC_SITE_URL)}" target="_blank" rel="noopener noreferrer">{esc(PUBLIC_SITE_HOST)}</a>
                <a class="topbar-chip" href="{esc(LIVE_ZOOM_URL)}" target="_blank" rel="noopener noreferrer">Join live</a>
                <a class="topbar-chip" href="{esc(build_whatsapp_url('Hi Matrika Academy, I need help with classes or admissions.'))}" target="_blank" rel="noopener noreferrer">Support</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        logo_src = logo_data_uri()
        logo_markup = (
            f"<img src='{logo_src}' alt='Matrika Academy logo' />"
            if logo_src
            else "<div class='brand-fallback'>M</div>"
        )
        st.markdown(
            f"""
            <div class="sidebar-card">
                <div class="sidebar-brand">
                    {logo_markup}
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

        if st.session_state.page == "Admin":
            st.markdown(
                """
                <div class="sidebar-card">
                    <div class="card-kicker">Team admin open</div>
                    <p class="card-copy">You are in the protected admin area. Use the button below to return to the public academy view.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button(
                "Back to academy",
                key="sidebar_back_home",
                use_container_width=True,
                on_click=jump_to,
                args=("Dashboard",),
            )
        else:
            st.radio(
                "Navigate",
                NAV_PAGE_NAMES,
                key=PAGE_WIDGET_KEY,
                label_visibility="collapsed",
                on_change=sync_page_from_navigation,
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

        learner = current_learner_profile()
        if learner_authenticated():
            st.markdown(
                f"""
                <div class="sidebar-card">
                    <div class="card-kicker">Learner account</div>
                    <p class="card-copy"><strong>{esc(learner.get("full_name") or "Matrika learner")}</strong></p>
                    <p class="card-copy">{esc(learner.get("email") or "")}</p>
                    <p class="card-copy">Automatic replies and saved forms are tied to this account.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            account_cols = st.columns(2)
            with account_cols[0]:
                st.button(
                    "Open account",
                    key="sidebar_account",
                    use_container_width=True,
                    on_click=jump_to,
                    args=("Account",),
                )
            with account_cols[1]:
                if st.button("Log out", key="sidebar_logout", use_container_width=True):
                    logout_learner()
                    jump_to("Dashboard")
                    st.rerun()
        else:
            st.markdown(
                """
                <div class="sidebar-card">
                    <div class="card-kicker">Learner account</div>
                    <p class="card-copy">Create or log into your account before you book classes, save payments, or contact the academy through protected forms.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button(
                "Create / login",
                key="sidebar_account_entry",
                use_container_width=True,
                on_click=jump_to,
                args=("Account",),
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

        st.markdown(
            """
            <div class="sidebar-card">
                <div class="card-kicker">Team access</div>
                <p class="card-copy">Admin tools stay out of the public navigation, but the Matrika team can still unlock them here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Open team admin",
            key="sidebar_admin",
            use_container_width=True,
            on_click=jump_to,
            args=("Admin",),
        )


def dashboard_page() -> None:
    left, right = st.columns([1.35, 0.95])
    with left:
        st.markdown(
            """
            <div class="hero-card">
                <span class="eyebrow">Matrika Academy</span>
                <h1 class="hero-title">A calm yoga space for learning, breath, and growth.</h1>
                <p class="hero-copy">
                    Keep yoga classes, guided practice, admissions, replays, and mentorship in one
                    serene place for mothers, children, and future teachers.
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

    render_illustration_panel("Dashboard")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    render_metric_grid(HOME_STATS)
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    render_interactive_pathfinder(
        "dashboard",
        eyebrow="Interactive guide",
        title="Find your best Matrika path in a few taps.",
        body="Choose who the journey is for, the best time period, and the learning style. The site will immediately suggest the best next step and matching live rhythm.",
        show_schedule_preview=True,
        show_related_programs=False,
    )

    if not learner_authenticated():
        render_section(
            "First visit",
            "A more premium landing path for new visitors.",
            "If you are discovering Matrika Academy for the first time, this flow helps you understand the journey before you create an account or request a class.",
        )
        render_card_grid(VISITOR_WELCOME_CARDS, columns=3, class_name="timeline-card")
        visitor_actions = st.columns(3)
        with visitor_actions[0]:
            st.button(
                "Start with account",
                key="visitor_account_cta",
                use_container_width=True,
                on_click=jump_to,
                args=("Account",),
            )
        with visitor_actions[1]:
            st.button(
                "Explore programs",
                key="visitor_programs_cta",
                use_container_width=True,
                on_click=jump_to,
                args=("Programs",),
            )
        with visitor_actions[2]:
            st.link_button(
                "Message the academy",
                build_whatsapp_url(
                    "Hi Matrika Academy, I am a new visitor and want help choosing the right yoga path."
                ),
                use_container_width=True,
            )

    render_section(
        "Public launch",
        "A cleaner way to share the academy with anyone.",
        "The academy now has a public-facing flow that feels calmer for first-time visitors and stronger for returning learners.",
    )
    launch_cols = st.columns([1.05, 0.95])
    with launch_cols[0]:
        render_card(
            PUBLIC_SITE_HOST,
            "Use the branded public site link when you want to invite families, students, or teachers into the academy experience.",
            kicker="Share-ready",
            meta=["Brand link", "Public", "Mobile"],
            class_name="feature-card",
        )
    with launch_cols[1]:
        st.link_button("Open public site", PUBLIC_SITE_URL, use_container_width=True)
        st.link_button(
            "Share on WhatsApp",
            build_whatsapp_url(f"Explore Matrika Academy here: {PUBLIC_SITE_URL}"),
            use_container_width=True,
        )
        st.link_button(
            "Email the academy link",
            build_mailto_url(
                "Matrika Academy",
                f"Hi, you can open Matrika Academy here: {PUBLIC_SITE_URL}",
            ),
            use_container_width=True,
        )

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
        "Public release strengths",
        "The current version is built to be easier to trust, easier to share, and easier to use from another device.",
        "These are the parts that make the academy feel more like a real public platform and less like an internal tool.",
    )
    render_card_grid(PUBLIC_RELEASE_CARDS, columns=3)

    render_section(
        "Designed around real users",
        "Parents, children, and future teachers each need a different kind of clarity.",
        "The app now gives each group a cleaner entry point into the academy.",
    )
    render_card_grid(OUTCOME_CARDS, columns=3)

    render_section(
        "How the journey works",
        "The academy flow is simple enough for first-time learners and structured enough for long-term growth.",
        "Use this as the path from enquiry to ongoing practice.",
    )
    render_steps(ADMISSIONS_STEPS)

    render_section(
        "Questions people usually ask first",
        "A few quick answers before someone commits to a class or enquiry.",
        "This helps first-time visitors feel oriented as soon as they land.",
    )
    render_card_grid(FAQ_CARDS, columns=3)


def account_page() -> None:
    render_section(
        "Learner account",
        "Create your account once, then log in whenever you want to use the academy tools.",
        "Protected sections now use learner accounts so submissions, automatic replies, and follow-up stay tied to the right person.",
    )
    render_illustration_panel("Account")

    if learner_authenticated():
        learner = current_learner_profile()
        render_card(
            learner.get("full_name") or "Matrika learner",
            "You are signed in. Protected forms will prefill your account details and automatic replies will go to this email.",
            kicker="Logged in",
            meta=[
                learner.get("email") or "No email",
                learner.get("phone") or "Phone optional",
                "Protected access enabled",
            ],
            class_name="info-card",
        )
        action_cols = st.columns(3)
        with action_cols[0]:
            st.button(
                "Go to admissions",
                key="account_to_admissions",
                use_container_width=True,
                on_click=jump_to,
                args=("Admissions",),
            )
        with action_cols[1]:
            st.button(
                "Open live studio",
                key="account_to_live",
                use_container_width=True,
                on_click=jump_to,
                args=("Live Studio",),
            )
        with action_cols[2]:
            if st.button("Log out now", key="account_logout", use_container_width=True):
                logout_learner()
                send_user_home(
                    kind="info",
                    title="You have been logged out",
                    body="Your learner session is closed. You can log in again anytime from the account page.",
                )
        st.info(
            "Your learner account keeps admissions, attendance, payments, and support messages tied to one email so the academy can reply automatically and follow up faster."
        )
        st.divider()
        render_section(
            "Linked payment apps",
            "Save the payment app you usually use so the academy can verify proofs faster.",
            "This does not charge anything automatically. It simply keeps your preferred third-party payment app and handle connected to your learner account.",
        )
        payment_cols = st.columns([0.95, 1.05])
        with payment_cols[0]:
            if preferred_payment_app(learner):
                render_card(
                    preferred_payment_app(learner),
                    preferred_payment_handle(learner) or "No handle saved yet.",
                    kicker="Linked payment profile",
                    meta=[
                        "Reusable in payments",
                        "Third-party app",
                        learner.get("linked_payment_notes") or "No extra note",
                    ],
                    class_name="info-card",
                )
            else:
                render_card(
                    "No payment app linked yet",
                    "Link your usual app if you want payment forms to remember the provider you use most often.",
                    kicker="Linked payment profile",
                    meta=["Google Pay", "PhonePe", "Paytm"],
                    class_name="info-card",
                )
            payment_button_cols = st.columns(2)
            with payment_button_cols[0]:
                st.button(
                    "Open payments",
                    key="account_to_payments",
                    use_container_width=True,
                    on_click=jump_to,
                    args=("Payments",),
                )
            with payment_button_cols[1]:
                st.link_button(
                    "Open UPI now",
                    payment_app_link(preferred_payment_app(learner) or "UPI", learner),
                    use_container_width=True,
                )
        with payment_cols[1]:
            render_form_banner(
                "&#10050;",
                "Link a preferred payment app",
                "Connect the provider name and your payer handle or UPI ID so future payment submissions feel faster and more consistent.",
            )
            current_app = preferred_payment_app(learner)
            app_index = PAYMENT_APP_OPTIONS.index(current_app) if current_app in PAYMENT_APP_OPTIONS else 0
            with st.form("payment_link_form"):
                linked_app = st.selectbox("Payment app", PAYMENT_APP_OPTIONS, index=app_index)
                linked_handle = st.text_input(
                    "UPI ID / wallet number",
                    value=preferred_payment_handle(learner),
                )
                linked_note = st.text_area(
                    "Note for the academy (optional)",
                    value=str(learner.get("linked_payment_notes", "")),
                )
                submit = st.form_submit_button("Save payment app")

                if submit:
                    clean_handle = normalize_payment_handle(linked_handle)
                    clean_note = normalize_text(linked_note)
                    if not clean_handle:
                        st.error("Add your UPI ID, wallet number, or payer handle.")
                    else:
                        updated_account = update_user_account(
                            learner.get("email", ""),
                            {
                                "linked_payment_app": linked_app,
                                "linked_payment_handle": clean_handle,
                                "linked_payment_notes": clean_note,
                                "linked_payment_updated_at": current_timestamp(),
                            },
                        )
                        if updated_account:
                            sync_learner_session(updated_account)
                        st.success("Your preferred payment app is linked to this learner account.")
        return

    create_col, login_col = st.columns(2)

    with create_col:
        render_card(
            "Create learner account",
            "Use your main email so the academy can send automatic replies, confirmations, and account-based follow-up.",
            kicker="Sign up",
            meta=["One-time setup", "Email-based access", "Protected forms"],
            class_name="timeline-card",
        )
        render_form_banner(
            "&#2384;",
            "Begin with a calm account setup",
            "This short sign-up keeps your yoga journey, saved forms, and academy replies connected to one learner profile.",
        )
        with st.form("create_account_form"):
            full_name = st.text_input("Full name")
            email = st.text_input("Email")
            phone = st.text_input("Phone (optional)")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            submit = st.form_submit_button("Create account")

            if submit:
                clean_name = normalize_text(full_name)
                clean_email = normalize_email(email)
                clean_phone = normalize_phone(phone)

                if not clean_name or not clean_email or not password or not confirm_password:
                    st.error("Please complete all required fields.")
                elif not valid_email(clean_email):
                    st.error("Enter a valid email address.")
                elif phone and not valid_phone(phone):
                    st.error("Enter a valid phone number or leave it blank.")
                elif not valid_password(password):
                    st.error(f"Use a password with at least {LEARNER_PASSWORD_MIN_LENGTH} characters.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                elif find_user_account(clean_email) and recent_account_creation_matches(clean_email):
                    existing_account = find_user_account(clean_email)
                    if existing_account:
                        sync_learner_session(existing_account)
                        send_user_home(
                            kind="success",
                            title="Learner account created",
                            body="Your account is ready and you can now use the protected parts of the academy.",
                        )
                elif find_user_account(clean_email):
                    st.error("An account with this email already exists. Please log in instead.")
                else:
                    account = create_user_account(clean_name, clean_email, clean_phone, password)
                    remember_recent_account_creation(clean_email)
                    sync_learner_session(account)
                    email_result = send_automatic_reply(
                        trigger="account_created",
                        page="Account",
                        to_email=clean_email,
                        recipient_name=clean_name,
                        subject="Welcome to Matrika Academy",
                        submission_title="learner account setup",
                        details=[
                            ("Created at", account["created_at"]),
                            ("Email", clean_email),
                            ("Phone", clean_phone or "Not shared"),
                        ],
                        next_steps="You can now log in on any device, book sessions, submit payments, and use the protected academy forms with this account.",
                        account_email=clean_email,
                        intro_text="Your Matrika Academy learner account is ready.",
                    )
                    send_user_home(
                        kind="success",
                        title="Learner account created",
                        body="Your account is ready and you can now use the protected parts of the academy.",
                        email_result=email_result,
                    )

    with login_col:
        render_card(
            "Log into your account",
            "Use the same email and password you created for the academy. Once you sign in, protected pages will use your saved account details.",
            kicker="Login",
            meta=["Protected access", "Saved details", "Automatic replies"],
            class_name="timeline-card",
        )
        render_form_banner(
            "&#10047;",
            "Return to your practice calmly",
            "Log in with the same academy email so your protected forms, check-ins, and replies stay in one place.",
        )
        with st.form("login_account_form"):
            email = st.text_input("Account email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Log in")

            if submit:
                clean_email = normalize_email(email)
                if not clean_email or not password:
                    st.error("Email and password are required.")
                elif not valid_email(clean_email):
                    st.error("Enter a valid email address.")
                else:
                    account = authenticate_user_account(clean_email, password)
                    if not account:
                        st.error("Incorrect email or password.")
                    else:
                        sync_learner_session(account)
                        login_email_result = send_automatic_reply(
                            trigger="login_alert",
                            page="Account",
                            to_email=clean_email,
                            recipient_name=str(account.get("full_name", "")).strip() or "Matrika learner",
                            subject="Matrika Academy login alert",
                            submission_title="account login",
                            details=[
                                ("Login time", current_timestamp()),
                                ("Account email", clean_email),
                            ],
                            next_steps="If this login was you, no action is needed. If it was not you, reset your password from the account page right away.",
                            account_email=clean_email,
                            intro_text="A new login to your Matrika Academy learner account was detected.",
                        )
                        send_user_home(
                            kind="success",
                            title="Welcome back",
                            body="You are logged in and the protected academy tools are ready for you.",
                            email_result=login_email_result,
                        )

        st.markdown("<div style='height:0.95rem'></div>", unsafe_allow_html=True)
        render_card(
            "Forgot your password?",
            "Request a six-digit verification code by email, then set a new password right here.",
            kicker="Reset access",
            meta=[f"{PASSWORD_RESET_CODE_LENGTH}-digit code", f"{PASSWORD_RESET_TTL_MINUTES}-minute expiry", "Email verification"],
            class_name="timeline-card",
        )
        render_form_banner(
            "&#10048;",
            "Verify by email and reset calmly",
            "We will send a short verification code to your learner email. Enter it below with a new password to restore access.",
        )
        if not smtp_configured():
            render_card(
                "Password reset email is temporarily unavailable",
                "The learner account is safe, but automated reset emails cannot be sent until academy mail delivery is reconnected. Use WhatsApp or email below and the team can help you restore access manually.",
                kicker="Support fallback",
                meta=["WhatsApp", "Email", "Manual recovery"],
                class_name="info-card",
            )
            render_support_actions(
                "Matrika Academy password help",
                "Hi Matrika Academy, I need help restoring access to my learner account because the password reset email is not available right now.",
                include_call=False,
            )
            st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
        default_reset_email = str(st.session_state.get("password_reset_email", "")).strip()
        reset_request_col, reset_verify_col = st.columns(2)
        with reset_request_col:
            with st.form("password_reset_request_form"):
                reset_email = st.text_input("Learner email", value=default_reset_email, key="password_reset_email_input")
                request_submit = st.form_submit_button("Send verification code")

                if request_submit:
                    clean_reset_email = normalize_email(reset_email)
                    st.session_state.password_reset_email = clean_reset_email
                    if not clean_reset_email:
                        st.error("Enter the learner email linked to your account.")
                    elif not valid_email(clean_reset_email):
                        st.error("Enter a valid email address.")
                    elif not smtp_configured():
                        st.info("Password reset by email is temporarily unavailable. Please use WhatsApp or email support and the academy will help restore access.")
                    else:
                        account = find_user_account(clean_reset_email)
                        if not account:
                            st.info("If an account exists for this email, a verification code will be sent.")
                        else:
                            reset_code, request_row = create_password_reset_request(clean_reset_email)
                            reset_email_result = send_automatic_reply(
                                trigger="password_reset_requested",
                                page="Account",
                                to_email=clean_reset_email,
                                recipient_name=str(account.get("full_name", "")).strip() or "Matrika learner",
                                subject="Matrika Academy password reset code",
                                submission_title="password reset request",
                                details=[
                                    ("Requested at", request_row["requested_at"]),
                                    ("Verification code", reset_code),
                                    ("Valid for", f"{PASSWORD_RESET_TTL_MINUTES} minutes"),
                                ],
                                next_steps="Enter this verification code in the password reset form inside the Matrika Academy app and choose a new password. If you did not request this, you can ignore the email.",
                                account_email=clean_reset_email,
                                intro_text="We received a request to reset your Matrika Academy learner password.",
                            )
                            delivered, message = reset_email_result
                            if delivered:
                                st.success(f"Verification code sent to {clean_reset_email}.")
                            else:
                                log_runtime_issue(message)
                                st.info("The verification email could not be sent right now. Please use academy support and we will help restore access.")

        with reset_verify_col:
            with st.form("password_reset_verify_form"):
                verify_email = st.text_input("Email for reset", value=default_reset_email, key="password_reset_verify_email")
                verification_code_input = st.text_input("Verification code", max_chars=PASSWORD_RESET_CODE_LENGTH)
                new_password = st.text_input("New password", type="password")
                confirm_new_password = st.text_input("Confirm new password", type="password")
                verify_submit = st.form_submit_button("Reset password")

                if verify_submit:
                    clean_verify_email = normalize_email(verify_email)
                    clean_code = digits_only(verification_code_input)
                    st.session_state.password_reset_email = clean_verify_email

                    if not clean_verify_email or not clean_code or not new_password or not confirm_new_password:
                        st.error("Complete all password reset fields.")
                    elif not valid_email(clean_verify_email):
                        st.error("Enter a valid email address.")
                    elif len(clean_code) != PASSWORD_RESET_CODE_LENGTH:
                        st.error(f"Enter the {PASSWORD_RESET_CODE_LENGTH}-digit verification code from the email.")
                    elif not valid_password(new_password):
                        st.error(f"Use a password with at least {LEARNER_PASSWORD_MIN_LENGTH} characters.")
                    elif new_password != confirm_new_password:
                        st.error("Passwords do not match.")
                    else:
                        verified, message, request_row = verify_password_reset_code(clean_verify_email, clean_code)
                        if not verified or request_row is None:
                            st.error(message)
                        else:
                            updated_account = reset_user_password(clean_verify_email, new_password, request_row)
                            if not updated_account:
                                st.error("We could not update the password for that learner account.")
                            else:
                                sync_learner_session(updated_account)
                                reset_confirmation_result = send_automatic_reply(
                                    trigger="password_reset_completed",
                                    page="Account",
                                    to_email=clean_verify_email,
                                    recipient_name=str(updated_account.get("full_name", "")).strip() or "Matrika learner",
                                    subject="Matrika Academy password updated",
                                    submission_title="password reset confirmation",
                                    details=[
                                        ("Updated at", current_timestamp()),
                                        ("Account email", clean_verify_email),
                                    ],
                                    next_steps="Your password has been updated and you are now signed in. If you did not make this change, contact the academy team immediately.",
                                    account_email=clean_verify_email,
                                    intro_text="Your Matrika Academy learner password was updated successfully.",
                                )
                                send_user_home(
                                    kind="success",
                                    title="Password updated",
                                    body="Your password has been reset and you are now signed in.",
                                    email_result=reset_confirmation_result,
                                )


def programs_page() -> None:
    render_section(
        "Academy tracks",
        "Structured journeys for every stage of learning.",
        "From pregnancy support to playful children's classes and mentoring for future teachers, the app keeps every path clear.",
    )
    render_illustration_panel("Programs")
    render_interactive_pathfinder(
        "programs",
        eyebrow="Interactive fit finder",
        title="Let the academy recommend the right program first.",
        body="This finder keeps the browsing experience more interactive by turning interest into a suggested path, instead of making learners scan every card manually.",
        show_schedule_preview=False,
        show_related_programs=True,
    )
    st.divider()
    render_program_comparison()
    st.divider()
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
    render_illustration_panel("Schedule")
    render_card_grid(SCHEDULE_HIGHLIGHTS, columns=3, class_name="schedule-card")
    st.divider()

    need_options = ["All journeys"] + journey_need_options()
    default_need = str(st.session_state.get(JOURNEY_STATE_KEY, ""))
    need_index = need_options.index(default_need) if default_need in need_options else 0
    time_options = ["All periods"] + TIME_PERIOD_OPTIONS
    default_time = str(st.session_state.get(JOURNEY_TIME_STATE_KEY, ""))
    time_index = time_options.index(default_time) if default_time in time_options else 0
    track_options = ["All tracks"] + sorted({row["Track"] for row in WEEKLY_SCHEDULE})

    render_section(
        "Interactive schedule explorer",
        "Filter the timetable by journey, time period, and track.",
        "This turns the schedule into a calmer planning tool instead of a static timetable.",
    )
    filter_cols = st.columns(3)
    with filter_cols[0]:
        selected_need = st.selectbox("Journey", need_options, index=need_index, key="schedule_need_filter")
    with filter_cols[1]:
        selected_time = st.selectbox("Time period", time_options, index=time_index, key="schedule_time_filter")
    with filter_cols[2]:
        selected_track = st.selectbox("Track", track_options, key="schedule_track_filter")

    active_need = None if selected_need == "All journeys" else selected_need
    if active_need:
        st.session_state[JOURNEY_STATE_KEY] = active_need
    if selected_time != "All periods":
        st.session_state[JOURNEY_TIME_STATE_KEY] = selected_time
    filtered_rows = schedule_rows_for_need(
        active_need,
        time_period="Flexible" if selected_time == "All periods" else selected_time,
        track="" if selected_track == "All tracks" else selected_track,
    )

    left, right = st.columns([1.2, 0.8])
    with left:
        st.caption(f"{len(filtered_rows)} live slot(s) match this view.")
        if filtered_rows:
            st.dataframe(filtered_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No current live slot matches that exact filter combination yet. The full timetable is still shown below for context.")
            st.dataframe(WEEKLY_SCHEDULE, use_container_width=True, hide_index=True)
    with right:
        if active_need:
            profile = journey_profile(active_need)
            render_card(
                str(profile.get("program_title", "")),
                str(profile.get("next_step", "")),
                kicker="Suggested next step",
                meta=[selected_time, str(profile.get("recommended_page", ""))],
                class_name="info-card",
            )
            st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
            st.button(
                str(profile.get("cta_label", "Open next step")),
                key="schedule_recommended_cta",
                use_container_width=True,
                on_click=open_page_with_journey,
                args=(str(profile.get("recommended_page", "Programs")), active_need, "Flexible" if selected_time == "All periods" else selected_time),
            )
            st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
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
    render_illustration_panel("Admissions")
    if not require_learner_account(
        "Admissions",
        "Create or log into your learner account before you request admissions so the academy can keep your batch details and automatic replies tied to one account.",
    ):
        return

    learner = current_learner_profile()
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
        st.caption(
            f"Signed in as {learner.get('email')}. Admissions requests and automatic replies will use this learner account."
        )
        render_form_banner(
            "&#10047;",
            "Share your seat request mindfully",
            "A few clear details help the academy suggest the right track, timing, and support path without back-and-forth.",
        )
        with st.form("booking_form"):
            full_name = st.text_input("Full name", value=learner.get("full_name", ""))
            email = st.text_input("Email", value=learner.get("email", ""), disabled=True)
            phone = st.text_input("Phone", value=learner.get("phone", ""))
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
            time_period = st.selectbox("Time period", TIME_PERIOD_OPTIONS)
            preferred_time = st.selectbox("Preferred time", ["Morning", "Afternoon", "Evening"])
            goals = st.text_area("What would you like help with?")
            notes = st.text_area("Health notes / availability (optional)")
            submit = st.form_submit_button("Request admission")

            if submit:
                clean_name = normalize_text(full_name)
                clean_email = normalize_email(learner.get("email", "") or email)
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
                    row = {
                        "submitted_at": current_timestamp(),
                        "page": "Admissions",
                        "account_name": learner.get("full_name", ""),
                        "account_email": learner.get("email", ""),
                        "name": clean_name,
                        "email": clean_email,
                        "phone": clean_phone,
                        "track": track,
                        "learner_stage": learner_stage,
                        "mode": mode,
                        "time_period": time_period,
                        "preferred_time": preferred_time,
                        "goals": clean_goals,
                        "notes": clean_notes,
                    }
                    if duplicate_submission_detected("bookings.csv", row):
                        send_user_home(
                            kind="info",
                            title="Admissions request already received",
                            body="We already saved this request, so there is no need to submit it again.",
                        )
                    save_row("bookings.csv", row)
                    email_result = send_automatic_reply(
                        trigger="admissions_request",
                        page="Admissions",
                        to_email=clean_email,
                        recipient_name=clean_name,
                        subject="Matrika Academy admission request received",
                        submission_title="admissions request",
                        details=[
                            ("Submitted at", row["submitted_at"]),
                            ("Track", track),
                            ("Learner stage", learner_stage),
                            ("Preferred mode", mode),
                            ("Time period", time_period),
                            ("Preferred time", preferred_time),
                        ],
                        next_steps="We will review your request and contact you with the best batch or session plan.",
                        account_email=learner.get("email", ""),
                    )
                    send_user_home(
                        kind="success",
                        title="Admissions request received",
                        body="Your request was saved and you have been returned to the home page.",
                        email_result=email_result,
                    )


def live_studio_page() -> None:
    render_section(
        "Live studio",
        "Join live sessions, access replays, and record attendance.",
        "This area keeps the live teaching experience organized and easy to revisit.",
    )
    render_illustration_panel("Live Studio")
    if not require_learner_account(
        "Live Studio",
        "Create or log into your learner account before you open live links, replay requests, or attendance so the academy can keep your class history together.",
    ):
        return

    learner = current_learner_profile()
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
        st.caption(
            f"Signed in as {learner.get('email')}. Attendance and replay support will be tied to this learner account."
        )
        render_form_banner(
            "&#10048;",
            "Mark your class presence gently",
            "Saving attendance helps the academy connect your live session, replay support, and follow-up guidance to the right learner profile.",
        )
        with st.form("attendance_form"):
            attendee_name = st.text_input("Name", value=learner.get("full_name", ""))
            attendee_email = st.text_input("Email", value=learner.get("email", ""), disabled=True)
            session = st.selectbox(
                "Session",
                ["Garbhasanskara", "Trimester", "Prenatal", "Postnatal", "Kids", "Teacher Training"],
            )
            mode = st.selectbox("Mode", ["Live", "Replay"])
            time_period = st.selectbox("Time period", TIME_PERIOD_OPTIONS)
            submit = st.form_submit_button("Save attendance")

            if submit:
                clean_name = normalize_text(attendee_name)
                clean_email = normalize_email(learner.get("email", "") or attendee_email)

                if not clean_name or not clean_email:
                    st.error("Name and email are required.")
                elif not valid_email(clean_email):
                    st.error("Enter a valid email address.")
                else:
                    row = {
                        "submitted_at": current_timestamp(),
                        "page": "Live Studio",
                        "account_name": learner.get("full_name", ""),
                        "account_email": learner.get("email", ""),
                        "name": clean_name,
                        "email": clean_email,
                        "session": session,
                        "mode": mode,
                        "time_period": time_period,
                    }
                    if duplicate_submission_detected("attendance.csv", row):
                        send_user_home(
                            kind="info",
                            title="Attendance already received",
                            body="We already saved this attendance entry, so there is no need to submit it again.",
                        )
                    save_row("attendance.csv", row)
                    email_result = send_automatic_reply(
                        trigger="attendance_saved",
                        page="Live Studio",
                        to_email=clean_email,
                        recipient_name=clean_name,
                        subject="Matrika Academy attendance recorded",
                        submission_title="attendance update",
                        details=[
                            ("Submitted at", row["submitted_at"]),
                            ("Session", session),
                            ("Mode", mode),
                            ("Time period", time_period),
                        ],
                        next_steps="Your attendance has been recorded. If you need the replay or a class link, reply to this email.",
                        account_email=learner.get("email", ""),
                    )
                    send_user_home(
                        kind="success",
                        title="Attendance saved",
                        body="Your attendance was recorded and you have been returned to the home page.",
                        email_result=email_result,
                    )


def certification_page() -> None:
    render_section(
        "Certification",
        "Mentored training for future Matrika teachers.",
        "This pathway blends practice teaching, feedback loops, and specialty work with mothers and children.",
    )
    render_illustration_panel("Certification")
    if not require_learner_account(
        "Certification",
        "Create or log into your learner account before you apply so your certification journey, automatic replies, and mentor follow-up stay connected.",
    ):
        return

    learner = current_learner_profile()
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
        st.caption(
            f"Signed in as {learner.get('email')}. Certification applications and automatic replies will use this learner account."
        )
        render_form_banner(
            "&#2384;",
            "Apply with intention",
            "Share your current practice level and teaching goals so the mentor team can guide your certification journey thoughtfully.",
        )
        with st.form("training_form"):
            full_name = st.text_input("Full name", value=learner.get("full_name", ""))
            email = st.text_input("Email", value=learner.get("email", ""), disabled=True)
            time_period = st.selectbox("Time period", TIME_PERIOD_OPTIONS)
            experience = st.selectbox(
                "Experience",
                ["Beginner", "Practitioner (1+ yr)", "Intermediate", "Advanced"],
            )
            motivation = st.text_area("Why do you want to teach?")
            submit = st.form_submit_button("Apply")

            if submit:
                clean_name = normalize_text(full_name)
                clean_email = normalize_email(learner.get("email", "") or email)
                clean_motivation = normalize_text(motivation)

                if not clean_name or not clean_email:
                    st.error("Name and email are required.")
                elif not valid_email(clean_email):
                    st.error("Enter a valid email address.")
                else:
                    row = {
                        "submitted_at": current_timestamp(),
                        "page": "Certification",
                        "account_name": learner.get("full_name", ""),
                        "account_email": learner.get("email", ""),
                        "name": clean_name,
                        "email": clean_email,
                        "time_period": time_period,
                        "experience": experience,
                        "motivation": clean_motivation,
                    }
                    if duplicate_submission_detected("training_applications.csv", row):
                        send_user_home(
                            kind="info",
                            title="Certification application already received",
                            body="We already saved this application, so there is no need to submit it again.",
                        )
                    save_row("training_applications.csv", row)
                    email_result = send_automatic_reply(
                        trigger="certification_application",
                        page="Certification",
                        to_email=clean_email,
                        recipient_name=clean_name,
                        subject="Matrika Academy certification application received",
                        submission_title="certification application",
                        details=[
                            ("Submitted at", row["submitted_at"]),
                            ("Time period", time_period),
                            ("Experience", experience),
                        ],
                        next_steps="Our mentors will review your application and reach out with the next steps.",
                        account_email=learner.get("email", ""),
                    )
                    send_user_home(
                        kind="success",
                        title="Certification application received",
                        body="Your application was saved and you have been returned to the home page.",
                        email_result=email_result,
                    )


def kids_page() -> None:
    render_section(
        "Kids studio",
        "Movement, stories, and calm-down breath for ages 5-14.",
        "The experience is designed to keep children engaged without feeling rushed or overwhelmed.",
    )
    render_illustration_panel("Kids Studio")
    if not require_learner_account(
        "Kids Studio",
        "Create or log into your learner account before you send a kids enquiry so the academy can reply automatically and keep parent communication in one place.",
    ):
        return

    learner = current_learner_profile()
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
    st.caption(
        f"Signed in as {learner.get('email')}. Kids enquiries and automatic replies will use this learner account."
    )
    render_form_banner(
        "&#10047;",
        "Plan a joyful kids practice",
        "Use this enquiry to share your child details and the best time window for your family so the academy can suggest the right batch.",
    )
    with st.form("kids_form"):
        parent = st.text_input("Parent / Guardian name", value=learner.get("full_name", ""))
        child = st.text_input("Child name")
        age = st.number_input("Child age", min_value=3, max_value=18, step=1)
        email = st.text_input("Contact email", value=learner.get("email", ""), disabled=True)
        time_period = st.selectbox("Time period", TIME_PERIOD_OPTIONS)
        submit = st.form_submit_button("Enroll or enquire")

        if submit:
            clean_parent = normalize_text(parent)
            clean_child = normalize_text(child)
            clean_email = normalize_email(learner.get("email", "") or email)

            if not clean_parent or not clean_child or not clean_email:
                st.error("Parent name, child name, and email are required.")
            elif not valid_email(clean_email):
                st.error("Enter a valid email address.")
            else:
                row = {
                    "submitted_at": current_timestamp(),
                    "page": "Kids Studio",
                    "account_name": learner.get("full_name", ""),
                    "account_email": learner.get("email", ""),
                    "parent": clean_parent,
                    "child": clean_child,
                    "age": age,
                    "email": clean_email,
                    "time_period": time_period,
                }
                if duplicate_submission_detected("kids_enquiries.csv", row):
                    send_user_home(
                        kind="info",
                        title="Kids enquiry already received",
                        body="We already saved this enquiry, so there is no need to submit it again.",
                    )
                save_row("kids_enquiries.csv", row)
                email_result = send_automatic_reply(
                    trigger="kids_enquiry",
                    page="Kids Studio",
                    to_email=clean_email,
                    recipient_name=clean_parent,
                    subject="Matrika Academy kids studio enquiry received",
                    submission_title="kids studio enquiry",
                    details=[
                        ("Submitted at", row["submitted_at"]),
                        ("Child name", clean_child),
                        ("Age", age),
                        ("Time period", time_period),
                    ],
                    next_steps="We will share the kids schedule, available session options, and joining details soon.",
                    account_email=learner.get("email", ""),
                )
                send_user_home(
                    kind="success",
                    title="Kids enquiry received",
                    body="Your enquiry was saved and you have been returned to the home page.",
                    email_result=email_result,
                )


def payments_page() -> None:
    render_section(
        "Tuition and payments",
        "Choose a plan and share proof when you are ready.",
        "The app keeps payment steps simple and transparent so the team can confirm your seat quickly.",
    )
    render_illustration_panel("Payments")
    if not require_learner_account(
        "Payments",
        "Create or log into your learner account before you submit payment proof so receipts, confirmations, and follow-up stay tied to your account email.",
    ):
        return

    learner = current_learner_profile()
    render_card_grid(PAYMENT_PLANS, columns=3, class_name="pricing-card")
    st.divider()

    linked_app = preferred_payment_app(learner)
    linked_handle = preferred_payment_handle(learner)
    provider_options = (
        [linked_app] + [option for option in PAYMENT_PROVIDER_OPTIONS if option != linked_app]
        if linked_app
        else PAYMENT_PROVIDER_OPTIONS
    )
    latest_link = st.session_state.get("latest_razorpay_link") or latest_razorpay_link(learner.get("email", ""))
    academy_upi_qr = payment_app_link(linked_app or "UPI", learner)

    left, right = st.columns([1.15, 0.85])
    with left:
        render_form_banner(
            "&#8377;",
            "Secure Razorpay checkout",
            "Create a live Razorpay payment link for the selected plan so learners can pay on a hosted checkout page instead of copying details manually.",
        )
        if razorpay_configured():
            plan_titles = [item["title"] for item in PAYMENT_PLANS]
            default_plan = plan_titles[0]
            with st.form("razorpay_payment_link_form"):
                checkout_name = st.text_input("Learner name", value=learner.get("full_name", ""))
                checkout_email = st.text_input("Learner email", value=learner.get("email", ""), disabled=True)
                checkout_phone = st.text_input("Phone", value=learner.get("phone", ""))
                checkout_time_period = st.selectbox("Time period", TIME_PERIOD_OPTIONS, key="razorpay_time_period")
                checkout_plan = st.selectbox("Plan", plan_titles, key="razorpay_plan")
                suggested_amount = payment_plan_amount(checkout_plan or default_plan) or 500
                checkout_amount = st.number_input(
                    "Amount to collect (INR)",
                    min_value=500,
                    max_value=100000,
                    value=suggested_amount,
                    step=100,
                    help="The amount is prefilled from the selected plan. Adjust it only if you are applying a scholarship, coupon, or a custom academy amount.",
                )
                checkout_provider_hint = st.selectbox(
                    "Preferred payment app",
                    provider_options,
                    help="This helps the academy remember whether the learner usually pays from Google Pay, PhonePe, Paytm, Razorpay, or another app.",
                )
                checkout_notes = st.text_area("Notes for the payment link", help="Optional batch, coupon, or billing note.")
                create_link = st.form_submit_button("Create secure Razorpay link")

                if create_link:
                    clean_name = normalize_text(checkout_name)
                    clean_email = normalize_email(learner.get("email", "") or checkout_email)
                    clean_phone = normalize_phone(checkout_phone)
                    clean_notes = normalize_text(checkout_notes)

                    if not clean_name or not clean_email:
                        st.error("Learner name and learner email are required.")
                    elif not valid_email(clean_email):
                        st.error("Enter a valid learner email before creating the Razorpay link.")
                    elif clean_phone and not valid_phone(clean_phone):
                        st.error("Enter a valid 10-digit Indian phone number or leave the phone field blank.")
                    else:
                        created, link_row, detail = create_razorpay_payment_link(
                            learner=learner,
                            name=clean_name,
                            email=clean_email,
                            phone=clean_phone,
                            plan=checkout_plan,
                            time_period=checkout_time_period,
                            amount_inr=int(checkout_amount),
                            provider_hint=checkout_provider_hint,
                            notes=clean_notes,
                        )
                        if not created or not link_row:
                            st.error(detail or "Razorpay could not create the payment link.")
                        else:
                            st.session_state.latest_razorpay_link = link_row
                            latest_link = link_row
                            email_result = send_automatic_reply(
                                trigger="razorpay_payment_link",
                                page="Payments",
                                to_email=clean_email,
                                recipient_name=clean_name,
                                subject="Matrika Academy Razorpay payment link",
                                submission_title="Razorpay payment link",
                                details=[
                                    ("Submitted at", link_row["created_at"]),
                                    ("Plan", checkout_plan),
                                    ("Time period", checkout_time_period),
                                    ("Amount", f"INR {int(checkout_amount)}"),
                                    ("Provider hint", checkout_provider_hint),
                                    ("Razorpay link", link_row.get("short_url", "")),
                                    ("Reference", link_row.get("reference_id", "")),
                                ],
                                next_steps="Open the Razorpay link, complete the payment on the hosted checkout page, and then return to this payment page if you want to add a note or share proof manually as well.",
                                account_email=learner.get("email", ""),
                                intro_text="We created a secure Razorpay checkout link for your Matrika Academy payment request.",
                            )
                            st.success("Razorpay link created. Open the secure checkout below.")
                            render_confirmation_result(email_result)
        else:
            render_card(
                "Razorpay is not connected yet",
                "Add Razorpay live keys in secrets or Render environment variables to generate hosted payment links from this page. Until then, the manual UPI and payment-proof flow still works.",
                kicker="Setup needed",
                meta=[RAZORPAY_KEY_ID_SECRET, RAZORPAY_KEY_SECRET_SECRET, "Hosted checkout"],
                class_name="info-card",
            )
        if latest_link:
            latest_status = str(latest_link.get("status", "created")).replace("_", " ").title()
            render_card(
                "Latest secure checkout",
                str(latest_link.get("short_url", "")) or "A Razorpay link was created for this learner account.",
                kicker=latest_status,
                meta=[
                    str(latest_link.get("plan", "No plan")),
                    f"INR {latest_link.get('amount', '')}",
                    str(latest_link.get("reference_id", "")) or "No reference",
                ],
                class_name="info-card",
            )
            latest_actions = st.columns(2)
            with latest_actions[0]:
                if latest_link.get("short_url"):
                    st.link_button(
                        "Open secure Razorpay checkout",
                        str(latest_link.get("short_url", "")),
                        use_container_width=True,
                    )
            with latest_actions[1]:
                if st.button("Refresh Razorpay status", use_container_width=True):
                    refreshed, updated_link, detail = refresh_razorpay_link_status(latest_link)
                    if not refreshed or not updated_link:
                        st.warning(detail or "Razorpay status could not be refreshed.")
                    else:
                        st.session_state.latest_razorpay_link = updated_link
                        st.success(f"Razorpay link status is now {updated_link.get('status', 'created')}.")
                        st.rerun()
        qr_cols = st.columns(2)
        with qr_cols[0]:
            render_payment_qr(
                "Scan UPI QR",
                academy_upi_qr,
                "Scan this on another device to open the Matrika Academy UPI payment destination.",
                meta=["UPI", PAYMENT_UPI_ID, linked_app or "Any UPI app"],
            )
        with qr_cols[1]:
            if latest_link and latest_link.get("short_url"):
                render_payment_qr(
                    "Scan Razorpay checkout",
                    str(latest_link.get("short_url", "")),
                    "Scan this from another device to open the secure hosted Razorpay checkout link.",
                    meta=[
                        str(latest_link.get("status", "created")).replace("_", " ").title(),
                        str(latest_link.get("plan", "No plan")),
                        f"INR {latest_link.get('amount', '')}",
                    ],
                )
            else:
                render_card(
                    "Razorpay QR appears after link creation",
                    "Create a secure Razorpay payment link above and the payment page will immediately show a scannable QR for that checkout.",
                    kicker="QR ready after link",
                    meta=["Hosted checkout", "Another-device scan", "Secure"],
                    class_name="info-card",
                )
        st.divider()
        payment_actions = st.columns(2)
        with payment_actions[0]:
            st.link_button(
                f"Open {linked_app}" if linked_app else "Open UPI payment",
                payment_app_link(linked_app or "UPI", learner),
                use_container_width=True,
            )
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
        render_section(
            "Manual payment fallback",
            "Choose the app you want to pay from if you are not using the secure Razorpay checkout above.",
            "These shortcuts keep the older UPI path available for learners who prefer a direct app-to-app flow.",
        )
        app_buttons = st.columns(2)
        for index, app_name in enumerate(PAYMENT_APP_OPTIONS[:4]):
            with app_buttons[index % 2]:
                st.link_button(
                    f"Pay with {app_name}",
                    payment_app_link(app_name, learner),
                    use_container_width=True,
                )
        if linked_app and linked_handle:
            st.caption(f"Linked payer profile: {linked_app} · {linked_handle}")
    with right:
        render_card(
            "Need an invoice?",
            f"Email {CONTACT_EMAIL} with your selected plan and GST details.",
            kicker="Billing",
            meta=["Invoice support", "GST ready"],
            class_name="info-card",
        )
        st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
        if razorpay_configured():
            current_mode = razorpay_mode()
            if current_mode == "test":
                render_card(
                    "Razorpay is in test mode",
                    "Checkout links can be created and scanned successfully, but they will not collect real payments until live Razorpay keys are added in the host environment.",
                    kicker="Test payments only",
                    meta=["rzp_test", "Safe for QA", "Switch to live keys later"],
                    class_name="info-card",
                )
                st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
            render_card(
                "Why Razorpay here?",
                "The hosted checkout keeps the payment step cleaner on mobile and desktop, while the academy still keeps your learner account, plan, and follow-up context connected.",
                kicker="Recommended",
                meta=["Hosted checkout", "Cards + UPI + netbanking", "Learner linked"],
                class_name="info-card",
            )
            st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
        if linked_app:
            render_card(
                linked_app,
                linked_handle or "Preferred payment handle saved in your learner account.",
                kicker="Linked payment app",
                meta=["Account connected", "Reusable", learner.get("linked_payment_notes") or "No note"],
                class_name="info-card",
            )
        else:
            render_card(
                "No app linked yet",
                "Link Google Pay, PhonePe, Paytm, BHIM, or another UPI app from the Account page for a smoother payment flow.",
                kicker="Payment linking",
                meta=["Account page", "Third-party apps", "Reusable"],
                class_name="info-card",
            )

    st.divider()
    render_section("Share payment proof", "Upload your payment reference so the team can verify it.", "Saved entries go to a CSV file for easy review.")
    st.caption(
        f"Signed in as {learner.get('email')}. Payment confirmations and automatic replies will use this learner account."
    )
    render_form_banner(
        "&#10050;",
        "Complete the payment step with clarity",
        "The academy only needs your chosen plan, amount, and transaction reference to verify your seat quickly and reply with the next step.",
    )
    with st.form("payment_form"):
        full_name = st.text_input("Name", value=learner.get("full_name", ""))
        email = st.text_input("Email", value=learner.get("email", ""), disabled=True)
        time_period = st.selectbox("Time period", TIME_PERIOD_OPTIONS)
        plan = st.selectbox("Plan", [item["title"] for item in PAYMENT_PLANS])
        amount = st.number_input(
            "Amount paid (INR)",
            min_value=500,
            max_value=100000,
            value=payment_plan_amount(plan) or 500,
            step=100,
        )
        method = st.selectbox("Method", ["Razorpay", "UPI", "Card", "NetBanking", "Wallet"])
        provider = st.selectbox("Payment app / provider", provider_options)
        payer_handle = st.text_input(
            "Your payer handle",
            value=linked_handle,
            help="Example: your UPI ID, wallet number, or the account handle you used in the payment app.",
        )
        reference = st.text_input("Payment reference / UPI transaction ID")
        notes = st.text_area("Notes (batch, time, coupon)")
        submit = st.form_submit_button("Submit proof")

        if submit:
            clean_name = normalize_text(full_name)
            clean_email = normalize_email(learner.get("email", "") or email)
            clean_payer_handle = normalize_payment_handle(payer_handle)
            clean_reference = normalize_text(reference)
            clean_notes = normalize_text(notes)

            if not clean_name or not clean_email or not clean_reference:
                st.error("Name, email, and payment reference are required.")
            elif not valid_email(clean_email):
                st.error("Enter a valid email address.")
            elif method in {"UPI", "Wallet"} and provider != RAZORPAY_PROVIDER_NAME and not clean_payer_handle:
                st.error("Add the payer handle or app account you used for this payment.")
            else:
                row = {
                    "submitted_at": current_timestamp(),
                    "page": "Payments",
                    "account_name": learner.get("full_name", ""),
                    "account_email": learner.get("email", ""),
                    "name": clean_name,
                    "email": clean_email,
                    "time_period": time_period,
                    "plan": plan,
                    "amount": amount,
                    "method": method,
                    "provider": provider,
                    "payer_handle": clean_payer_handle,
                    "reference": clean_reference,
                    "notes": clean_notes,
                }
                if duplicate_submission_detected("payments.csv", row):
                    send_user_home(
                        kind="info",
                        title="Payment proof already received",
                        body="We already saved this payment proof, so there is no need to submit it again.",
                    )
                save_row("payments.csv", row)
                email_result = send_automatic_reply(
                    trigger="payment_proof",
                    page="Payments",
                    to_email=clean_email,
                    recipient_name=clean_name,
                    subject="Matrika Academy payment proof received",
                    submission_title="payment proof",
                        details=[
                            ("Submitted at", row["submitted_at"]),
                            ("Time period", time_period),
                            ("Plan", plan),
                            ("Amount", f"INR {amount}"),
                            ("Method", method),
                            ("Payment app", provider),
                            ("Payer handle", clean_payer_handle or "Not shared"),
                            ("Reference", clean_reference),
                        ],
                        next_steps="We will verify the payment and confirm your seat on email or WhatsApp.",
                        account_email=learner.get("email", ""),
                    )
                send_user_home(
                    kind="success",
                    title="Payment proof received",
                    body="Your payment entry was saved and you have been returned to the home page.",
                    email_result=email_result,
                )


def contact_page() -> None:
    render_section(
        "Connect",
        "Reach the team by email, phone, or the form below.",
        "We keep replies friendly and quick so families and teachers always know the next step.",
    )
    render_illustration_panel("Contact")
    if not require_learner_account(
        "Contact",
        "Create or log into your learner account before you send support messages so the academy can keep every reply tied to the right learner profile.",
    ):
        return

    learner = current_learner_profile()
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
        st.caption(
            f"Signed in as {learner.get('email')}. Contact messages and automatic replies will use this learner account."
        )
        render_form_banner(
            "&#10047;",
            "Send one clear message",
            "Your support note stays connected to the same learner account the academy already sees in admissions, attendance, and payments.",
        )
        with st.form("contact_form"):
            full_name = st.text_input("Name", value=learner.get("full_name", ""))
            email = st.text_input("Email", value=learner.get("email", ""), disabled=True)
            time_period = st.selectbox("Time period", TIME_PERIOD_OPTIONS)
            message = st.text_area("Message")
            submit = st.form_submit_button("Send message")

            if submit:
                clean_name = normalize_text(full_name)
                clean_email = normalize_email(learner.get("email", "") or email)
                clean_message = normalize_text(message)

                if not clean_name or not clean_email or not clean_message:
                    st.error("Please complete all fields.")
                elif not valid_email(clean_email):
                    st.error("Enter a valid email address.")
                else:
                    row = {
                        "submitted_at": current_timestamp(),
                        "page": "Contact",
                        "account_name": learner.get("full_name", ""),
                        "account_email": learner.get("email", ""),
                        "name": clean_name,
                        "email": clean_email,
                        "time_period": time_period,
                        "message": clean_message,
                    }
                    if duplicate_submission_detected("contact_messages.csv", row):
                        send_user_home(
                            kind="info",
                            title="Message already received",
                            body="We already saved this message, so there is no need to submit it again.",
                        )
                    save_row("contact_messages.csv", row)
                    email_result = send_automatic_reply(
                        trigger="contact_message",
                        page="Contact",
                        to_email=clean_email,
                        recipient_name=clean_name,
                        subject="Matrika Academy message received",
                        submission_title="support message",
                        details=[
                            ("Submitted at", row["submitted_at"]),
                            ("Time period", time_period),
                            ("Message", clean_message),
                        ],
                        next_steps="We have received your message and will reply as soon as possible.",
                        account_email=learner.get("email", ""),
                    )
                    send_user_home(
                        kind="success",
                        title="Message received",
                        body="Your message was saved and you have been returned to the home page.",
                        email_result=email_result,
                    )


def admin_page() -> None:
    render_section(
        "Admin",
        "See submission flow, storage status, and recent entries.",
        "This view is meant for the Matrika team to monitor enquiries and confirm that persistence is working.",
    )
    render_illustration_panel("Admin")

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
                f"The admin page is not fully protected yet. Add `{ADMIN_PASSWORD_SECRET}` in Streamlit secrets or host env vars."
            )
        render_form_banner(
            "&#10047;",
            "Open the academy control room",
            "Admin access stays separate from the public learner journey so academy data remains protected and easy to review.",
        )
        with st.form("admin_login_form"):
            password = st.text_input("Admin password", type="password")
            submit = st.form_submit_button("Unlock admin")
            if submit:
                expected = str(get_secret_value(ADMIN_PASSWORD_SECRET, "")).strip()
                if not expected:
                    st.error("Admin password is not configured in secrets or environment variables yet.")
                elif password == expected:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect admin password.")
        return

    if google_persistence_enabled() and not st.session_state.get("admin_sheets_initialized", False):
        ensure_google_submission_sheets()
        st.session_state.admin_sheets_initialized = True

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
    source_summary = [
        {"source": name, "rows": len(load_submission_rows(name))}
        for name in submission_files
    ]
    if source_summary:
        st.caption("Submission summary")
        st.dataframe(source_summary, use_container_width=True, hide_index=True)
    runtime_issues = list(st.session_state.get("runtime_issues", []))
    if runtime_issues:
        st.caption("Recent runtime notices")
        st.dataframe(runtime_issues[::-1], use_container_width=True, hide_index=True)
    st.divider()

    if not submission_files:
        st.info("No submission files exist yet. Once users start sending forms, they will appear here.")
        return

    selected_file = st.selectbox("Submission source", submission_files)
    rows = load_submission_rows(selected_file)
    admin_rows = sanitize_rows_for_admin(selected_file, rows)

    if not admin_rows:
        st.info(f"No entries found in `{selected_file}` yet.")
        return

    action_cols = st.columns([0.4, 0.3, 0.3])
    with action_cols[0]:
        st.download_button(
            "Download CSV",
            data=rows_to_csv_bytes(admin_rows),
            file_name=selected_file,
            mime="text/csv",
            use_container_width=True,
        )
    with action_cols[1]:
        sheet_url = google_sheet_url()
        if sheet_url:
            st.link_button("Open Google Sheet", sheet_url, use_container_width=True)
    with action_cols[2]:
        if st.button("Refresh data", use_container_width=True):
            st.rerun()

    st.caption(f"{len(admin_rows)} saved entries in `{selected_file}`")
    st.dataframe(admin_rows[::-1], use_container_width=True, hide_index=True)


PAGE_ROUTES = {
    "Dashboard": dashboard_page,
    "Account": account_page,
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
    st.session_state.setdefault(PAGE_WIDGET_KEY, PAGE_NAMES[0])
    st.session_state.setdefault("recent_submissions", {})
    st.session_state.setdefault("learner_authenticated", False)
    st.session_state.setdefault("learner_name", "")
    st.session_state.setdefault("learner_email", "")
    st.session_state.setdefault("learner_phone", "")
    st.session_state.setdefault("sheets_initialized", False)
    st.session_state.setdefault("admin_sheets_initialized", False)
    st.session_state.setdefault("latest_razorpay_link", {})
    st.session_state.setdefault("runtime_issues", [])
    if st.session_state.page not in PAGE_NAMES:
        st.session_state.page = PAGE_NAMES[0]
    if st.session_state.page in NAV_PAGE_NAMES:
        st.session_state[PAGE_WIDGET_KEY] = st.session_state.page
    elif st.session_state.get(PAGE_WIDGET_KEY) not in NAV_PAGE_NAMES:
        st.session_state[PAGE_WIDGET_KEY] = PAGE_NAMES[0]


def main() -> None:
    apply_theme()
    initialize_state()
    render_sidebar()
    render_topbar()
    render_flash_notice()
    PAGE_ROUTES[st.session_state.page]()
    render_footer()


if __name__ == "__main__":
    main()
