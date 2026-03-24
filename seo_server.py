from __future__ import annotations

import asyncio
import contextlib
import html
import json
import os
import subprocess
from collections.abc import AsyncIterator
from pathlib import Path
from urllib.parse import quote

import httpx
import websockets
from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse

APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "assets" / "matrika_logo.svg"
BUDDHA_PATH = APP_DIR / "assets" / "buddha_meditation.svg"

PUBLIC_SITE_URL = os.getenv("PUBLIC_SITE_URL", "https://matrikayogaacademy.com").rstrip("/")
APP_BASE_PATH = os.getenv("APP_BASE_PATH", "/app").rstrip("/") or "/app"
APP_BASE_SEGMENT = APP_BASE_PATH.lstrip("/")
INTERNAL_STREAMLIT_PORT = int(os.getenv("STREAMLIT_INTERNAL_PORT", "8501"))
STREAMLIT_HTTP_BASE = f"http://127.0.0.1:{INTERNAL_STREAMLIT_PORT}"
STREAMLIT_WS_BASE = f"ws://127.0.0.1:{INTERNAL_STREAMLIT_PORT}"
CONTACT_PHONE = "7893939545"
CONTACT_EMAIL = "drpeddamandadi@gmail.com"
CEO_NAME = "Abhinav"
MD_NAME = "Dr. Lavanya"
LIVE_ZOOM_URL = "https://us04web.zoom.us/j/8048675666?pwd=KF3fzQ5y1ZaDibDafMrbWHyCHl2jqV.1"
WHATSAPP_URL = f"https://wa.me/917893939545?text={quote('Hi Matrika Academy, I want help choosing the right yoga path.')}"

PROGRAMS = [
    ("Garbhasanskara Flow", "Gentle breath, grounding, and pregnancy-aware movement with live and replay support."),
    ("Prenatal + Postnatal Care", "Recovery-aware sessions designed for comfort, healing rhythm, and steadier routine building."),
    ("Kids Yoga Studio", "Playful movement, stories, balance work, and calmer focus for children."),
    ("Teacher Certification", "Mentored training with sequencing, practicum, and supportive feedback."),
]

PRICING_HINTS = [
    ("Garbhasanskara Flow", "INR 4,200", "Pregnancy-aware grounding with live classes, replays, and guided follow-through."),
    ("Prenatal + Postnatal Care", "INR 3,200", "Comfort-led recovery and care rhythms for mothers who need flexibility."),
    ("Kids Yoga Studio", "INR 2,800", "Playful, focus-building movement for children with parent-friendly support."),
    ("Teacher Certification", "INR 24,000", "Mentored training, practice teaching, and a more supported certification route."),
]

WHY_US_POINTS = [
    (
        "Typical class links",
        "Jumping between messages, links, and separate follow-up often makes new learners feel uncertain.",
        "A calmer academy flow keeps discovery, admission, class links, payments, and support in one place.",
    ),
    (
        "Busy family schedules",
        "Rigid class-only systems make it hard for mothers, parents, and trainees to stay consistent.",
        "Live sessions are paired with replay support, so progress can continue even on busy weeks.",
    ),
    (
        "First-time confidence",
        "Many yoga sites explain the offer but do not help people choose the right path with clarity.",
        "The website and academy guide learners toward prenatal, postnatal, kids, or teacher training with softer decisions.",
    ),
]

EXPERIENCE_SIGNALS = [
    (
        "Small-batch care",
        "Learners usually choose Matrika for calmer batches, more guided support, and a less crowded digital experience.",
    ),
    (
        "Live plus replay",
        "Families can attend live and still continue with replay support when life, parenting, or work shifts the day.",
    ),
    (
        "Human follow-through",
        "The journey keeps real contact points through WhatsApp, email, and structured next steps instead of leaving people unsure.",
    ),
]

FAQS = [
    (
        "What kinds of yoga classes does Matrika Academy offer?",
        "Matrika Academy offers prenatal yoga, postnatal recovery support, kids yoga, live online classes, and teacher training.",
    ),
    (
        "Can learners join classes online from any device?",
        "Yes. Learners can open the academy online, join live sessions, and continue with replay support from desktop or mobile.",
    ),
    (
        "How do admissions and payments work?",
        "Learners can choose a path, create an account, request admission, and then complete payment through the academy payment flow.",
    ),
    (
        "Is there a free trial or a live preview before joining?",
        "Yes. Families can request a free live preview or demo conversation over WhatsApp before choosing the right yoga path.",
    ),
    (
        "Do classes include replay access?",
        "Yes. The academy is designed around live guidance with replay continuity so learners can keep going even when a class time is missed.",
    ),
    (
        "Are classes suitable for pregnant mothers and postnatal recovery?",
        "Yes. Matrika Yoga Academy includes pregnancy-aware and recovery-aware pathways so mothers can move with more comfort and steadier support.",
    ),
    (
        "Can parents enquire for children without creating a full account first?",
        "Yes. Families can understand the offering from the website first and then move into the academy flow when they are ready to enrol.",
    ),
    (
        "Who leads the academy?",
        "Matrika Yoga Academy is led by Abhinav, CEO, and Dr. Lavanya, Managing Director, with a care-first teaching and digital experience.",
    ),
    (
        "How much do classes usually cost?",
        "Program pricing varies by path, but the website now shares pricing hints so families can understand the approximate investment before they enquire.",
    ),
    (
        "Can I join from Android, iPhone, or desktop?",
        "Yes. The academy can be opened on desktop or mobile browsers, and learners can continue classes, payments, and follow-up from any device.",
    ),
]

SEO_CONTENT_PAGES = {
    "prenatal-yoga": {
        "title": "Prenatal Yoga Classes Online | Matrika Yoga Academy",
        "description": "Explore guided prenatal yoga classes online with live support, replay access, and calm trimester-aware practice at Matrika Yoga Academy.",
        "eyebrow": "Prenatal care",
        "headline": "Prenatal yoga that feels calm, supported, and easy to continue.",
        "intro": "Matrika Yoga Academy offers prenatal classes online for learners who want breath-led movement, gentler rhythm, and a more supported digital experience from home.",
        "points": [
            "Trimester-aware sequences and guided breath",
            "Live classes with replay support for busy schedules",
            "A calmer route into the academy app for admissions and follow-up",
        ],
    },
    "postnatal-yoga": {
        "title": "Postnatal Recovery Yoga Online | Matrika Yoga Academy",
        "description": "Discover online postnatal recovery yoga with careful movement, breathing support, and a calmer routine-building path at Matrika Yoga Academy.",
        "eyebrow": "Postnatal recovery",
        "headline": "Postnatal yoga designed for recovery, comfort, and steadier routine building.",
        "intro": "The postnatal experience at Matrika keeps recovery practical and low-pressure, with online access, replay support, and more guided next steps.",
        "points": [
            "Recovery-aware sessions with gentler progression",
            "Guidance for comfort, mobility, and returning to rhythm",
            "Support that continues through the academy app after joining",
        ],
    },
    "kids-yoga-classes": {
        "title": "Kids Yoga Classes Online | Matrika Yoga Academy",
        "description": "Find online kids yoga classes with playful movement, focus-building routines, and parent-friendly follow-up at Matrika Yoga Academy.",
        "eyebrow": "Kids yoga",
        "headline": "Kids yoga that feels playful, focused, and parent-friendly from the first visit.",
        "intro": "The kids yoga path is designed to help children move, focus, and enjoy the class rhythm while giving parents a clearer, calmer digital journey.",
        "points": [
            "Movement, stories, and calm-building routines",
            "Ages 5 to 14 with parent-friendly follow-up",
            "Simple enquiry and scheduling support through the academy app",
        ],
    },
    "yoga-teacher-training": {
        "title": "Yoga Teacher Training Online | Matrika Yoga Academy",
        "description": "Explore online yoga teacher training with mentorship, practice teaching, and cohort guidance at Matrika Yoga Academy.",
        "eyebrow": "Teacher training",
        "headline": "Teacher training that feels mentored, modern, and steady.",
        "intro": "Matrika's certification path supports future teachers with sequencing, practicum, feedback, and a clearer digital journey from interest to cohort.",
        "points": [
            "Mentored feedback and supervised practice",
            "A clearer view of progression, timing, and readiness",
            "Protected academy tools for applications, payments, and follow-up",
        ],
    },
}

streamlit_process: subprocess.Popen[str] | None = None


def esc(value: object) -> str:
    return html.escape(str(value))


def site_host() -> str:
    return PUBLIC_SITE_URL.removeprefix("https://").removeprefix("http://")


def academy_app_url() -> str:
    return f"{PUBLIC_SITE_URL}{APP_BASE_PATH}/"


def academy_embedded_app_url() -> str:
    return f"{academy_app_url()}?academy_embed=1"


def academy_shell_url() -> str:
    return f"{PUBLIC_SITE_URL}/academy"


def seo_page_url(slug: str) -> str:
    return f"{PUBLIC_SITE_URL}/{slug}"


def json_ld_payload() -> str:
    payload = [
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Matrika Yoga Academy",
            "url": PUBLIC_SITE_URL,
            "logo": f"{PUBLIC_SITE_URL}/assets/matrika_logo.svg",
            "email": CONTACT_EMAIL,
            "telephone": CONTACT_PHONE,
            "description": "Matrika Yoga Academy offers online prenatal yoga, postnatal support, kids yoga, and yoga teacher training.",
        },
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "Matrika Yoga Academy",
            "url": PUBLIC_SITE_URL,
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{academy_shell_url()}",
                "query-input": "required name=academy_path",
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": answer,
                    },
                }
                for question, answer in FAQS
            ],
        },
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def academy_shell_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Opening Matrika Academy</title>
    <meta name="robots" content="noindex,nofollow" />
    <meta name="theme-color" content="#F7F0E8" />
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:wght@400;500;700;800&display=swap');
      :root {{
        --bg: #f7f0e8;
        --bg-soft: #fbf5ef;
        --bg-deep: #f0dfd2;
        --ink: #3d2b1f;
        --muted: #705c4d;
        --pista: #8fa876;
        --forest: #4a6741;
        --terracotta: #c4785a;
        --blush: #e8a882;
        --line: rgba(74, 103, 65, 0.13);
        --card: rgba(255, 250, 245, 0.84);
        --shadow: 0 24px 64px rgba(86, 58, 42, 0.12);
      }}
      * {{ box-sizing: border-box; }}
      @view-transition {{
        navigation: auto;
      }}
      ::view-transition-group(*),
      ::view-transition-old(*),
      ::view-transition-new(*) {{
        animation-duration: 0.6s;
        animation-timing-function: cubic-bezier(0.19, 1, 0.22, 1);
      }}
      body {{
        margin: 0;
        font-family: "DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at 10% 10%, rgba(196, 120, 90, 0.16), transparent 24%),
          radial-gradient(circle at 82% 10%, rgba(143, 168, 118, 0.22), transparent 20%),
          linear-gradient(160deg, var(--bg), var(--bg-soft) 52%, var(--bg-deep));
      }}
      .loader {{
        position: fixed;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
        background: rgba(247, 240, 232, 0.96);
        z-index: 20;
        transition: opacity .6s ease, visibility .6s ease;
      }}
      .loader.hidden {{
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
      }}
      .card {{
        width: min(92vw, 460px);
        border-radius: 32px;
        border: 1px solid var(--line);
        background:
          radial-gradient(circle at top, rgba(232, 168, 130, 0.18), transparent 34%),
          var(--card);
        padding: 1.5rem;
        text-align: center;
        box-shadow: var(--shadow);
        backdrop-filter: blur(20px);
      }}
      .card img {{
        width: 72px;
        height: 72px;
        border-radius: 22px;
      }}
      .card h1 {{
        margin: 0.9rem 0 0.5rem;
        font-family: "Cormorant Garamond", serif;
        font-size: clamp(2.1rem, 5vw, 3.1rem);
        line-height: 0.96;
        letter-spacing: -0.04em;
        color: var(--forest);
      }}
      .spinner {{
        width: 84px;
        height: 84px;
        margin: 1.1rem auto 0;
        border-radius: 999px;
        background:
          radial-gradient(circle at center, rgba(247, 240, 232, 0.94) 0 28%, transparent 29%),
          conic-gradient(
            from 0deg,
            rgba(196, 120, 90, 0.08),
            rgba(196, 120, 90, 0.94),
            rgba(232, 168, 130, 0.7),
            rgba(143, 168, 118, 0.5),
            rgba(74, 103, 65, 0.86),
            rgba(196, 120, 90, 0.08)
          );
        box-shadow: inset 0 0 0 11px rgba(255, 250, 245, 0.9), 0 18px 42px rgba(86, 58, 42, 0.12);
        animation: petal-spin 4.6s ease-in-out infinite;
      }}
      .status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.45rem 0.85rem;
        border-radius: 999px;
        background: rgba(143, 168, 118, 0.14);
        color: var(--forest);
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }}
      .status-pill::before {{
        content: "";
        width: 0.5rem;
        height: 0.5rem;
        border-radius: 50%;
        background: var(--terracotta);
        animation: breath-pulse 2.8s ease-in-out infinite;
      }}
      .copy {{
        color: var(--muted);
        line-height: 1.7;
      }}
      iframe {{
        position: fixed;
        inset: 0;
        width: 100%;
        height: 100%;
        border: 0;
        background: var(--bg);
      }}
      .fallback {{
        margin-top: 1rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.88rem 1.1rem;
        border-radius: 999px;
        text-decoration: none;
        color: #fff;
        border: 1px solid rgba(255,255,255,0.12);
        background: linear-gradient(135deg, var(--terracotta), var(--blush));
        box-shadow: 0 16px 34px rgba(164, 96, 69, 0.2);
        transition: transform 0.6s ease, box-shadow 0.6s ease;
      }}
      .fallback:hover {{
        transform: translateY(-2px);
        box-shadow: 0 20px 42px rgba(164, 96, 69, 0.24);
      }}
      @keyframes petal-spin {{
        0%, 100% {{ transform: rotate(0deg) scale(0.98); }}
        50% {{ transform: rotate(180deg) scale(1.04); }}
      }}
      @keyframes breath-pulse {{
        0%, 100% {{ transform: scale(0.9); opacity: 0.55; }}
        50% {{ transform: scale(1.15); opacity: 1; }}
      }}
    </style>
  </head>
  <body>
    <div class="loader" id="loader">
      <div class="card">
        <span class="status-pill">Guiding you in</span>
        <img src="{PUBLIC_SITE_URL}/assets/matrika_logo.svg" alt="Matrika Academy logo" />
        <h1>Opening Matrika Academy</h1>
        <p class="copy">
          The academy space is loading in a calmer, more intentional way, so families do not have to sit inside
          the default Streamlit skeleton screen.
        </p>
        <div class="spinner" aria-hidden="true"></div>
        <a class="fallback" href="{academy_app_url()}" target="_self">Open the app directly</a>
      </div>
    </div>
    <iframe id="academy-frame" src="{academy_embedded_app_url()}" title="Matrika Academy app"></iframe>
    <script>
      var loader = document.getElementById('loader');
      var frame = document.getElementById('academy-frame');
      var minimumDelayDone = false;
      var frameReady = false;
      function maybeHideLoader() {{
        if (minimumDelayDone && frameReady && loader) {{
          loader.classList.add('hidden');
        }}
      }}
      window.setTimeout(function () {{
        minimumDelayDone = true;
        maybeHideLoader();
      }}, 1400);
      if (frame) {{
        frame.addEventListener('load', function () {{
          window.setTimeout(function () {{
            frameReady = true;
            maybeHideLoader();
          }}, 450);
        }});
      }}
      window.setTimeout(function () {{
        if (loader) {{
          loader.querySelector('.copy').textContent =
            'The academy is still warming up. This can happen after inactivity on the current hosting plan, but the app should appear shortly.';
        }}
      }}, 6000);
    </script>
  </body>
</html>
"""


def landing_page_html() -> str:
    hero_stats = [
        ("12", "+", "live batches every week"),
        ("4", "", "core academy paths"),
        ("100", "%", "online access with replay"),
        ("1", "", "calm place to manage it all"),
    ]
    ritual_steps = [
        ("01", "Choose your path", "Start with prenatal care, postnatal rhythm, kids yoga, or teacher training."),
        ("02", "Join the live flow", "Use the academy app for admissions, schedules, classes, and steady guidance."),
        ("03", "Continue with support", "Replay access, payments, and human follow-through stay in one calm system."),
    ]
    marquee_items = [
        "Live + replay support",
        "Prenatal grounding",
        "Postnatal recovery rhythm",
        "Kids yoga focus",
        "Teacher training",
        "Guided admissions",
        "Online from any device",
        "Small batch attention",
    ]
    floating_tokens = [
        ("Live cohorts", "12%", "12%", "18", "0.1s"),
        ("Replay ready", "66%", "15%", "24", "0.5s"),
        ("Calm progress", "14%", "70%", "15", "0.25s"),
        ("Mentored support", "58%", "76%", "20", "0.75s"),
    ]
    hero_stats_markup = "".join(
        f"""
        <article class="stat-card reveal" style="--delay:{index * 0.08:.2f}s;">
          <strong>{esc(value)}{esc(suffix)}</strong>
          <span>{esc(label)}</span>
        </article>
        """
        for index, (value, suffix, label) in enumerate(hero_stats, start=1)
    )
    program_cards = "".join(
        f"""
        <article class="program-card reveal" style="--delay:{index * 0.08:.2f}s;">
            <span class="card-kicker">Path {index:02d}</span>
            <h3>{esc(title)}</h3>
            <p>{esc(body)}</p>
        </article>
        """
        for index, (title, body) in enumerate(PROGRAMS, start=1)
    )
    ritual_cards = "".join(
        f"""
        <article class="journey-card reveal" style="--delay:{index * 0.08:.2f}s;">
          <span class="journey-number">{esc(number)}</span>
          <h3>{esc(title)}</h3>
          <p>{esc(body)}</p>
        </article>
        """
        for index, (number, title, body) in enumerate(ritual_steps, start=1)
    )
    pricing_markup = "".join(
        f"""
        <article class="info-card pricing-card reveal" style="--delay:{index * 0.08:.2f}s;">
          <span class="card-kicker">Pricing hint</span>
          <h3>{esc(title)}</h3>
          <strong class="price-tag">{esc(price)}</strong>
          <p>{esc(note)}</p>
        </article>
        """
        for index, (title, price, note) in enumerate(PRICING_HINTS, start=1)
    )
    why_us_markup = "".join(
        f"""
        <article class="comparison-card reveal" style="--delay:{index * 0.08:.2f}s;">
          <span class="card-kicker">Why Matrika</span>
          <h3>{esc(title)}</h3>
          <div class="comparison-grid">
            <div class="comparison-col">
              <strong>Typical experience</strong>
              <p>{esc(typical)}</p>
            </div>
            <div class="comparison-col accent">
              <strong>Matrika approach</strong>
              <p>{esc(matrika)}</p>
            </div>
          </div>
        </article>
        """
        for index, (title, typical, matrika) in enumerate(WHY_US_POINTS, start=1)
    )
    experience_markup = "".join(
        f"""
        <article class="info-card experience-card reveal" style="--delay:{index * 0.08:.2f}s;">
          <span class="card-kicker">What families value</span>
          <h3>{esc(title)}</h3>
          <p>{esc(body)}</p>
        </article>
        """
        for index, (title, body) in enumerate(EXPERIENCE_SIGNALS, start=1)
    )
    faq_markup = "".join(
        f"""
        <details class="faq-item reveal" style="--delay:{index * 0.06:.2f}s;">
            <summary>{esc(question)}</summary>
            <p>{esc(answer)}</p>
        </details>
        """
        for index, (question, answer) in enumerate(FAQS, start=1)
    )
    marquee_markup = "".join(
        f"<span>{esc(item)}</span>"
        for item in marquee_items * 2
    )
    seo_cards = "".join(
        f"""
        <a class="program-card reveal seo-link-card" style="--delay:{index * 0.08:.2f}s;" href="{seo_page_url(slug)}">
            <span class="card-kicker">{esc(page["eyebrow"])}</span>
            <h3>{esc(page["headline"])}</h3>
            <p>{esc(page["description"])}</p>
        </a>
        """
        for index, (slug, page) in enumerate(SEO_CONTENT_PAGES.items(), start=1)
    )
    floating_markup = "".join(
        f"""
        <span
          class="floating-pill"
          data-depth="{esc(depth)}"
          style="--x:{esc(x)}; --y:{esc(y)}; --delay:{esc(delay)};"
        >{esc(label)}</span>
        """
        for label, x, y, depth, delay in floating_tokens
    )
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Matrika Yoga Academy | Prenatal Yoga, Kids Yoga and Teacher Training</title>
    <meta
      name="description"
      content="Matrika Yoga Academy offers online prenatal yoga, postnatal recovery yoga, kids yoga classes, and yoga teacher training with live and replay support."
    />
    <link rel="canonical" href="{PUBLIC_SITE_URL}/" />
    <link rel="icon" href="{PUBLIC_SITE_URL}/assets/matrika_logo.svg" type="image/svg+xml" />
    <meta name="theme-color" content="#F7F0E8" />
    <link rel="manifest" href="{PUBLIC_SITE_URL}/manifest.webmanifest" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="Matrika Yoga Academy" />
    <meta
      property="og:description"
      content="A calm online yoga academy for prenatal support, kids yoga, and teacher training."
    />
    <meta property="og:url" content="{PUBLIC_SITE_URL}/" />
    <meta property="og:image" content="{PUBLIC_SITE_URL}/assets/matrika_logo.svg" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="Matrika Yoga Academy" />
    <meta
      name="twitter:description"
      content="Online prenatal yoga, postnatal recovery support, kids yoga, and teacher training."
    />
    <script type="application/ld+json">
{json_ld_payload()}
    </script>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:wght@400;500;700;800&display=swap');
      :root {{
        --bg: #f7f0e8;
        --bg-soft: #fbf5ef;
        --bg-deep: #f0dfd2;
        --card: rgba(255, 250, 245, 0.8);
        --card-strong: rgba(255, 252, 248, 0.92);
        --ink: #3d2b1f;
        --muted: #705c4d;
        --pista: #8fa876;
        --pista-bright: #aac18e;
        --forest: #4a6741;
        --moss: #425339;
        --terracotta: #c4785a;
        --terracotta-deep: #a96045;
        --blush: #e8a882;
        --violet: #c4a8c8;
        --line: rgba(74, 103, 65, 0.13);
        --line-strong: rgba(74, 103, 65, 0.24);
        --shadow: 0 24px 72px rgba(86, 58, 42, 0.1);
        --shadow-soft: 0 14px 34px rgba(86, 58, 42, 0.07);
        --max-width: min(1220px, calc(100vw - 2rem));
      }}
      * {{ box-sizing: border-box; }}
      @view-transition {{
        navigation: auto;
      }}
      ::view-transition-group(*),
      ::view-transition-old(*),
      ::view-transition-new(*) {{
        animation-duration: 0.6s;
        animation-timing-function: cubic-bezier(0.19, 1, 0.22, 1);
      }}
      html {{ scroll-behavior: smooth; }}
      body {{
        margin: 0;
        font-family: "DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at 12% 10%, rgba(196, 120, 90, 0.14), transparent 26%),
          radial-gradient(circle at 88% 6%, rgba(143, 168, 118, 0.18), transparent 24%),
          linear-gradient(160deg, var(--bg), var(--bg-soft) 50%, var(--bg-deep));
        min-height: 100vh;
        overflow-x: hidden;
      }}
      body::before,
      body::after {{
        content: "";
        position: fixed;
        inset: auto;
        pointer-events: none;
        z-index: 0;
        border-radius: 999px;
        filter: blur(44px);
        opacity: 0.55;
      }}
      body::before {{
        width: 34vw;
        height: 34vw;
        top: -8vw;
        left: -10vw;
        background: rgba(232, 168, 130, 0.22);
        animation: matrika-orb-drift 18s ease-in-out infinite;
      }}
      body::after {{
        width: 30vw;
        height: 30vw;
        right: -8vw;
        bottom: -8vw;
        background: rgba(143, 168, 118, 0.2);
        animation: matrika-orb-drift 22s ease-in-out infinite reverse;
      }}
      a {{ color: inherit; }}
      .ambient {{
        position: fixed;
        inset: 0;
        pointer-events: none;
        overflow: hidden;
        z-index: 0;
      }}
      .ambient-orb,
      .ambient-grid {{
        position: absolute;
        inset: 0;
      }}
      .ambient-orb::before,
      .ambient-orb::after {{
        content: "";
        position: absolute;
        border-radius: 50%;
        filter: blur(44px);
      }}
      .ambient-orb::before {{
        width: 26rem;
        height: 26rem;
        top: 12%;
        right: -6rem;
        background: rgba(232, 168, 130, 0.14);
        animation: matrika-aura-float 19s ease-in-out infinite;
      }}
      .ambient-orb::after {{
        width: 18rem;
        height: 18rem;
        left: -4rem;
        bottom: 14%;
        background: rgba(143, 168, 118, 0.16);
        animation: matrika-aura-float 16s ease-in-out infinite reverse;
      }}
      .ambient-grid {{
        background-image:
          linear-gradient(rgba(73, 100, 65, 0.045) 1px, transparent 1px),
          linear-gradient(90deg, rgba(73, 100, 65, 0.045) 1px, transparent 1px);
        background-size: 64px 64px;
        mask-image: radial-gradient(circle at center, black 42%, transparent 88%);
        opacity: 0.35;
        animation: matrika-grid-pan 28s linear infinite;
      }}
      .scroll-progress {{
        position: fixed;
        inset: 0 0 auto;
        height: 3px;
        z-index: 40;
        background: rgba(255, 255, 255, 0.08);
      }}
      .scroll-progress span {{
        display: block;
        height: 100%;
        width: 0;
        transform-origin: left center;
        background: linear-gradient(90deg, var(--pista), var(--forest), var(--pista-bright));
        box-shadow: 0 0 18px rgba(173, 200, 123, 0.45);
      }}
      .shell {{
        position: relative;
        z-index: 1;
        width: var(--max-width);
        margin: 0 auto;
        padding: 1.1rem 0 4rem;
      }}
      .topbar {{
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: center;
        padding: 0.95rem 1.15rem;
        border: 1px solid rgba(255, 249, 243, 0.72);
        border-radius: 999px;
        background: rgba(255, 250, 245, 0.78);
        backdrop-filter: blur(22px);
        box-shadow: var(--shadow-soft);
        position: sticky;
        top: 1rem;
        z-index: 20;
      }}
      .menu {{
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-left: auto;
      }}
      .menu a {{
        text-decoration: none;
        color: var(--muted);
        font-size: 0.94rem;
        font-weight: 600;
        transition: color 0.25s ease, transform 0.25s ease;
      }}
      .menu a:hover {{
        color: var(--ink);
        transform: translateY(-1px);
      }}
      .brand {{
        display: flex;
        align-items: center;
        gap: 0.9rem;
        text-decoration: none;
        color: var(--ink);
      }}
      .brand img {{
        width: 60px;
        height: 60px;
        border-radius: 18px;
        box-shadow: 0 10px 24px rgba(77, 106, 63, 0.14);
      }}
      .brand strong {{
        display: block;
        font-family: "Cormorant Garamond", serif;
        font-size: 1.65rem;
        letter-spacing: -0.04em;
        color: var(--forest);
      }}
      .brand span {{
        color: var(--muted);
        font-size: 0.92rem;
      }}
      .actions {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.8rem;
      }}
      .button {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.45rem;
        padding: 0.9rem 1.2rem;
        border-radius: 999px;
        background: linear-gradient(135deg, var(--terracotta), var(--blush));
        color: #fff;
        text-decoration: none;
        font-weight: 700;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 16px 34px rgba(164, 96, 69, 0.16);
        position: relative;
        overflow: hidden;
        transition: transform 0.35s ease, box-shadow 0.35s ease, background 0.35s ease;
      }}
      .button::after {{
        content: "";
        position: absolute;
        inset: -140% auto -140% -34%;
        width: 34%;
        transform: rotate(18deg);
        background: linear-gradient(180deg, transparent, rgba(255, 255, 255, 0.55), transparent);
        animation: matrika-button-sheen 5.6s ease-in-out infinite;
      }}
      .button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 22px 42px rgba(164, 96, 69, 0.22);
      }}
      .button.secondary {{
        background: rgba(255, 252, 248, 0.82);
        color: var(--ink);
        border: 1px solid var(--line);
        box-shadow: none;
      }}
      .button.secondary::after {{
        display: none;
      }}
      .button.secondary:hover {{
        transform: translateY(-3px);
        border-color: var(--line-strong);
        box-shadow: var(--shadow-soft);
      }}
      .hero {{
        margin-top: 1.25rem;
        padding: clamp(1.6rem, 4vw, 3rem);
        border-radius: 38px;
        position: relative;
        overflow: hidden;
        background:
          radial-gradient(circle at 18% 16%, rgba(232, 168, 130, 0.2), transparent 24%),
          radial-gradient(circle at 82% 18%, rgba(143, 168, 118, 0.22), transparent 22%),
          linear-gradient(145deg, rgba(255, 252, 248, 0.96), rgba(243, 233, 221, 0.84));
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
      }}
      .hero::before,
      .hero::after {{
        content: "";
        position: absolute;
        border-radius: 50%;
        pointer-events: none;
      }}
      .hero::before {{
        right: -8%;
        top: -18%;
        width: min(32vw, 360px);
        height: min(32vw, 360px);
        background: radial-gradient(circle, rgba(184, 220, 132, 0.34), transparent 68%);
        filter: blur(10px);
        animation: matrika-aura-float 16s ease-in-out infinite;
      }}
      .hero::after {{
        right: -2rem;
        bottom: -2rem;
        width: min(26vw, 260px);
        height: min(34vw, 340px);
        background: url("{PUBLIC_SITE_URL}/assets/buddha_meditation.svg") center bottom / contain no-repeat;
        opacity: 0.16;
        pointer-events: none;
      }}
      .hero-grid {{
        display: grid;
        grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
        gap: clamp(1.4rem, 3vw, 2.2rem);
        align-items: center;
      }}
      .hero-copy,
      .hero-scene {{
        position: relative;
        z-index: 1;
      }}
      .eyebrow {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border-radius: 999px;
        padding: 0.35rem 0.7rem;
        background: rgba(143, 168, 118, 0.14);
        color: var(--forest);
        text-transform: uppercase;
        letter-spacing: 0.13em;
        font-size: 0.72rem;
        font-weight: 800;
      }}
      h1 {{
        font-family: "Cormorant Garamond", serif;
        font-size: clamp(2.4rem, 6vw, 4.8rem);
        line-height: 0.94;
        margin: 0.7rem 0 1rem;
        max-width: 10ch;
        letter-spacing: -0.075em;
      }}
      .hero p {{
        max-width: 62ch;
        font-size: 1.06rem;
        line-height: 1.82;
        color: var(--muted);
      }}
      .hero-copy .actions {{
        margin-top: 1.25rem;
      }}
      .hero-scene {{
        min-height: 480px;
        border-radius: 30px;
        border: 1px solid rgba(255, 255, 255, 0.58);
        background:
          radial-gradient(circle at 48% 34%, rgba(232, 168, 130, 0.28), transparent 32%),
          linear-gradient(180deg, rgba(255, 252, 248, 0.72), rgba(243, 233, 221, 0.58));
        overflow: hidden;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
      }}
      .scene-layer {{
        position: absolute;
        inset: 0;
      }}
      .scene-grid {{
        position: absolute;
        inset: 8% 10%;
        border-radius: 26px;
        background-image:
          linear-gradient(rgba(73, 100, 65, 0.05) 1px, transparent 1px),
          linear-gradient(90deg, rgba(73, 100, 65, 0.05) 1px, transparent 1px);
        background-size: 50px 50px;
        mask-image: radial-gradient(circle at center, black 44%, transparent 86%);
        opacity: 0.65;
        animation: matrika-grid-pan 22s linear infinite;
      }}
      .scene-ring {{
        position: absolute;
        inset: auto;
        border-radius: 999px;
        border: 1px solid rgba(73, 100, 65, 0.16);
        animation: matrika-breathe 8s ease-in-out infinite;
      }}
      .scene-ring.a {{
        width: 220px;
        height: 220px;
        top: 18%;
        left: 50%;
        transform: translateX(-50%);
      }}
      .scene-ring.b {{
        width: 310px;
        height: 310px;
        top: 8%;
        left: 50%;
        transform: translateX(-50%);
        animation-delay: 0.7s;
      }}
      .scene-ring.c {{
        width: 390px;
        height: 390px;
        top: -1%;
        left: 50%;
        transform: translateX(-50%);
        animation-delay: 1.4s;
      }}
      .scene-glow {{
        position: absolute;
        top: 14%;
        left: 50%;
        width: 270px;
        height: 270px;
        transform: translateX(-50%);
        border-radius: 50%;
        background: radial-gradient(circle, rgba(232, 168, 130, 0.34), rgba(232, 168, 130, 0.1) 46%, transparent 72%);
        filter: blur(8px);
        animation: matrika-breathe 9s ease-in-out infinite;
      }}
      .scene-buddha {{
        position: absolute;
        left: 50%;
        bottom: 10%;
        width: min(72%, 340px);
        aspect-ratio: 0.82;
        transform: translateX(-50%);
        background: url("{PUBLIC_SITE_URL}/assets/buddha_meditation.svg") center bottom / contain no-repeat;
        opacity: 0.9;
        filter: drop-shadow(0 24px 42px rgba(73, 100, 65, 0.16));
      }}
      .scene-floor {{
        position: absolute;
        left: 50%;
        bottom: 6%;
        width: 72%;
        height: 22px;
        transform: translateX(-50%);
        border-radius: 999px;
        background: radial-gradient(circle, rgba(122, 160, 95, 0.34), transparent 70%);
        filter: blur(10px);
      }}
      .floating-pill {{
        position: absolute;
        left: var(--x);
        top: var(--y);
        padding: 0.72rem 0.9rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid rgba(255, 255, 255, 0.86);
        box-shadow: var(--shadow-soft);
        color: var(--forest);
        font-size: 0.86rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        animation: matrika-float 6s ease-in-out infinite;
        animation-delay: var(--delay);
        backdrop-filter: blur(14px);
      }}
      .hero-stat-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.85rem;
        margin-top: 1.4rem;
      }}
      .stat-card {{
        padding: 1rem;
        border-radius: 22px;
        border: 1px solid rgba(255, 255, 255, 0.8);
        background: rgba(255, 255, 255, 0.68);
        box-shadow: var(--shadow-soft);
        backdrop-filter: blur(14px);
      }}
      .stat-card strong {{
        display: block;
        font-size: clamp(1.6rem, 3vw, 2.2rem);
        letter-spacing: -0.06em;
      }}
      .stat-card span {{
        display: block;
        color: var(--muted);
        font-size: 0.9rem;
        line-height: 1.5;
        margin-top: 0.25rem;
      }}
      .grid {{
        display: grid;
        gap: 1rem;
      }}
      .grid.two {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .grid.three {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }}
      .grid.faq-grid {{
        gap: 0.85rem;
      }}
      .marquee {{
        margin-top: 1rem;
        position: relative;
        border-radius: 999px;
        border: 1px solid rgba(255, 255, 255, 0.78);
        background: rgba(255, 255, 255, 0.6);
        overflow: hidden;
        backdrop-filter: blur(16px);
      }}
      .marquee::before,
      .marquee::after {{
        content: "";
        position: absolute;
        top: 0;
        bottom: 0;
        width: 18%;
        z-index: 1;
        pointer-events: none;
      }}
      .marquee::before {{
        left: 0;
        background: linear-gradient(90deg, rgba(246, 249, 241, 0.92), transparent);
      }}
      .marquee::after {{
        right: 0;
        background: linear-gradient(270deg, rgba(246, 249, 241, 0.92), transparent);
      }}
      .marquee-track {{
        display: flex;
        gap: 1.2rem;
        width: max-content;
        padding: 0.95rem 0;
        animation: matrika-ticker 28s linear infinite;
      }}
      .marquee-track span {{
        white-space: nowrap;
        padding: 0.42rem 0.8rem;
        border-radius: 999px;
        background: rgba(143, 168, 118, 0.14);
        color: var(--forest);
        font-size: 0.86rem;
        font-weight: 700;
      }}
      .section {{
        margin-top: 1.35rem;
        padding: 1.5rem;
        border-radius: 32px;
        background: var(--card);
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
        backdrop-filter: blur(18px);
      }}
      .section-head {{
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: end;
        margin-bottom: 1rem;
      }}
      .section-head p {{
        max-width: 34rem;
      }}
      .section h2 {{
        margin: 0.5rem 0 0.3rem;
        font-size: clamp(1.7rem, 3.4vw, 2.9rem);
        letter-spacing: -0.06em;
      }}
      .section p {{
        color: var(--muted);
        line-height: 1.7;
      }}
      .program-card,
      .info-card,
      .comparison-card,
      .faq-item,
      .journey-card,
      .contact-card,
      .seo-link-card {{
        padding: 1.2rem;
        border-radius: 24px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.72);
        box-shadow: var(--shadow-soft);
        transition: transform 0.4s ease, border-color 0.35s ease, box-shadow 0.35s ease, background 0.35s ease;
      }}
      .program-card:hover,
      .info-card:hover,
      .comparison-card:hover,
      .journey-card:hover,
      .contact-card:hover,
      .seo-link-card:hover {{
        transform: translateY(-8px);
        border-color: var(--line-strong);
        background: rgba(255,255,255,0.86);
        box-shadow: 0 22px 48px rgba(86, 58, 42, 0.12);
      }}
      .program-card h3,
      .info-card h3,
      .comparison-card h3,
      .journey-card h3,
      .contact-card h3 {{
        margin: 0 0 0.45rem;
        font-family: "Cormorant Garamond", serif;
        letter-spacing: -0.05em;
        font-size: 1.18rem;
      }}
      .card-kicker,
      .journey-number {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 3rem;
        padding: 0.4rem 0.72rem;
        border-radius: 999px;
        background: rgba(143, 168, 118, 0.14);
        color: var(--forest);
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.8rem;
      }}
      .journey-number {{
        min-width: unset;
      }}
      .journey-card {{
        min-height: 220px;
      }}
      .price-tag {{
        display: inline-flex;
        margin: 0.25rem 0 0.55rem;
        padding: 0.45rem 0.8rem;
        border-radius: 999px;
        background: rgba(196, 120, 90, 0.12);
        color: var(--terracotta-deep);
        font-size: 0.94rem;
        font-weight: 800;
        letter-spacing: 0.02em;
      }}
      .comparison-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.85rem;
        margin-top: 0.85rem;
      }}
      .comparison-col {{
        padding: 0.95rem;
        border-radius: 18px;
        background: rgba(255, 252, 248, 0.7);
        border: 1px solid var(--line);
      }}
      .comparison-col.accent {{
        background: linear-gradient(180deg, rgba(143, 168, 118, 0.12), rgba(255, 252, 248, 0.9));
      }}
      .comparison-col strong {{
        display: block;
        margin-bottom: 0.35rem;
      }}
      .journey-card p {{
        margin-bottom: 0;
      }}
      .seo-link-card {{
        text-decoration: none;
        color: inherit;
        display: block;
      }}
      .schedule-list {{
        margin: 0;
        padding-left: 1.15rem;
        color: var(--muted);
        line-height: 1.8;
      }}
      .schedule-list li {{
        margin-bottom: 0.18rem;
      }}
      .support-stack {{
        display: grid;
        gap: 0.9rem;
      }}
      .support-pill {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.95rem 1rem;
        border-radius: 20px;
        background: rgba(246, 249, 241, 0.94);
        border: 1px solid var(--line);
      }}
      .support-pill strong {{
        font-size: 0.98rem;
      }}
      .support-pill span {{
        color: var(--muted);
        font-size: 0.88rem;
      }}
      .faq-item {{
        overflow: hidden;
      }}
      .faq-item summary {{
        list-style: none;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
      }}
      .faq-item summary::-webkit-details-marker {{
        display: none;
      }}
      summary {{
        cursor: pointer;
        font-weight: 700;
      }}
      .faq-item summary::after {{
        content: "+";
        width: 1.8rem;
        height: 1.8rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: rgba(173, 200, 123, 0.18);
        color: var(--forest);
        font-size: 1.05rem;
        flex: 0 0 auto;
        transition: transform 0.3s ease, background 0.3s ease;
      }}
      .faq-item[open] summary::after {{
        transform: rotate(45deg);
        background: rgba(173, 200, 123, 0.26);
      }}
      .faq-item p {{
        margin: 0.85rem 0 0;
      }}
      .contact-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
      }}
      .contact-card {{
        min-height: 100%;
      }}
      .cta-band {{
        margin-top: 1rem;
        padding: 1.25rem;
        border-radius: 28px;
        background:
          linear-gradient(135deg, rgba(196, 120, 90, 0.16), rgba(255, 252, 248, 0.92));
        border: 1px solid rgba(196, 120, 90, 0.2);
        box-shadow: var(--shadow-soft);
      }}
      .cta-band h3 {{
        margin: 0 0 0.35rem;
        font-size: 1.35rem;
        letter-spacing: -0.05em;
      }}
      .footer {{
        margin-top: 1.4rem;
        text-align: center;
        color: var(--muted);
        font-size: 0.95rem;
      }}
      .floating-whatsapp {{
        position: fixed;
        right: 1.2rem;
        bottom: 1.2rem;
        z-index: 30;
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.9rem 1.05rem;
        border-radius: 999px;
        text-decoration: none;
        color: #fff;
        background: linear-gradient(135deg, var(--forest), var(--pista));
        box-shadow: 0 18px 36px rgba(74, 103, 65, 0.24);
        font-size: 0.92rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        transition: transform 0.6s ease, box-shadow 0.6s ease;
      }}
      .floating-whatsapp:hover {{
        transform: translateY(-4px);
        box-shadow: 0 22px 40px rgba(74, 103, 65, 0.28);
      }}
      .floating-whatsapp::before {{
        content: "●";
        font-size: 0.74rem;
      }}
      .reveal {{
        opacity: 0;
        transform: translate3d(0, 54px, 0) scale(0.985);
        transition:
          opacity 0.9s cubic-bezier(0.18, 1, 0.22, 1),
          transform 0.9s cubic-bezier(0.18, 1, 0.22, 1);
        transition-delay: var(--delay, 0s);
        will-change: transform, opacity;
      }}
      .reveal.is-visible,
      .reveal.reveal-visible {{
        opacity: 1;
        transform: translate3d(0, 0, 0) scale(1);
      }}
      .parallax {{
        transition: transform 0.18s ease-out;
        will-change: transform;
      }}
      @keyframes matrika-orb-drift {{
        0%, 100% {{ transform: translate3d(0, 0, 0) scale(1); }}
        50% {{ transform: translate3d(3vw, 2vw, 0) scale(1.08); }}
      }}
      @keyframes matrika-aura-float {{
        0%, 100% {{ transform: translate3d(0, 0, 0); }}
        50% {{ transform: translate3d(0, -22px, 0); }}
      }}
      @keyframes matrika-grid-pan {{
        from {{ transform: translateY(0); }}
        to {{ transform: translateY(-64px); }}
      }}
      @keyframes matrika-button-sheen {{
        0%, 12% {{ left: -34%; opacity: 0; }}
        18% {{ opacity: 0.8; }}
        30%, 100% {{ left: 130%; opacity: 0; }}
      }}
      @keyframes matrika-breathe {{
        0%, 100% {{ transform: translateX(-50%) scale(0.98); opacity: 0.54; }}
        50% {{ transform: translateX(-50%) scale(1.04); opacity: 1; }}
      }}
      @keyframes matrika-float {{
        0%, 100% {{ transform: translate3d(0, 0, 0); }}
        50% {{ transform: translate3d(0, -10px, 0); }}
      }}
      @keyframes matrika-ticker {{
        from {{ transform: translateX(0); }}
        to {{ transform: translateX(-50%); }}
      }}
      @media (max-width: 900px) {{
        .topbar,
        .grid.two,
        .grid.three,
        .hero-grid,
        .contact-grid,
        .hero-stat-grid,
        .comparison-grid {{
          grid-template-columns: 1fr;
          display: grid;
        }}
        .topbar {{
          border-radius: 28px;
        }}
        .menu {{
          order: 3;
          margin-left: 0;
          flex-wrap: wrap;
        }}
        .actions {{ justify-content: flex-start; }}
        .hero::after {{
          opacity: 0.12;
          width: 180px;
          height: 240px;
        }}
        .hero-scene {{
          min-height: 380px;
        }}
        .marquee::before,
        .marquee::after {{
          width: 12%;
        }}
      }}
      @media (max-width: 640px) {{
        .shell {{
          width: min(100vw - 1rem, 100%);
        }}
        .topbar,
        .hero,
        .section,
        .cta-band {{
          border-radius: 24px;
        }}
        .brand strong {{
          font-size: 1.1rem;
        }}
        .brand span {{
          font-size: 0.86rem;
        }}
        h1 {{
          max-width: none;
          font-size: clamp(2.3rem, 12vw, 3.4rem);
        }}
        .hero-stat-grid {{
          gap: 0.7rem;
        }}
        .stat-card {{
          padding: 0.95rem;
        }}
        .floating-pill {{
          font-size: 0.76rem;
          padding: 0.6rem 0.75rem;
        }}
        .floating-whatsapp {{
          right: 0.8rem;
          bottom: 0.85rem;
          padding: 0.82rem 0.96rem;
        }}
      }}
      @media (prefers-reduced-motion: reduce) {{
        *,
        *::before,
        *::after {{
          animation: none !important;
          transition: none !important;
          scroll-behavior: auto !important;
        }}
        .reveal {{
          opacity: 1;
          transform: none;
        }}
      }}
    </style>
  </head>
  <body>
    <div class="scroll-progress" aria-hidden="true"><span id="scroll-progress-bar"></span></div>
    <div class="ambient" aria-hidden="true">
      <div class="ambient-orb"></div>
      <div class="ambient-grid"></div>
    </div>
    <main class="shell">
      <header class="topbar reveal reveal-visible">
        <a class="brand" href="{PUBLIC_SITE_URL}/">
          <img src="{PUBLIC_SITE_URL}/assets/matrika_logo.svg" alt="Matrika Yoga Academy logo" />
          <div>
            <strong>Matrika Yoga Academy</strong>
            <span>Online prenatal yoga, kids yoga, and teacher training</span>
          </div>
        </a>
        <nav class="menu" aria-label="Section links">
          <a href="#programs">Programs</a>
          <a href="#pricing">Pricing</a>
          <a href="#why-us">Why us</a>
          <a href="#journey">Journey</a>
          <a href="#faq">FAQ</a>
          <a href="#contact">Contact</a>
        </nav>
        <nav class="actions" aria-label="Primary">
          <a class="button" href="{academy_shell_url()}">Open Academy App</a>
          <a class="button secondary" href="{WHATSAPP_URL}">Book free preview</a>
        </nav>
      </header>

      <section class="hero reveal reveal-visible">
        <div class="hero-grid">
          <div class="hero-copy">
            <span class="eyebrow">Sacred earth &amp; bloom</span>
            <h1>A nurturing online yoga academy for mothers, children, and future teachers.</h1>
            <p>
              Explore online prenatal yoga, postnatal recovery guidance, kids yoga classes, and yoga teacher
              training through a calmer, more guided experience that feels warm, trustworthy, and spiritually grounded.
            </p>
            <div class="actions">
              <a class="button" href="{academy_shell_url()}">Open the academy</a>
              <a class="button secondary" href="{WHATSAPP_URL}">Request a free demo</a>
              <a class="button secondary" href="tel:{CONTACT_PHONE}">Call {CONTACT_PHONE}</a>
            </div>
            <div class="hero-stat-grid">{hero_stats_markup}</div>
          </div>
          <div class="hero-scene" data-hero-scene>
            <div class="scene-layer scene-grid"></div>
            <div class="scene-layer scene-glow parallax" data-depth="8"></div>
            <div class="scene-ring a parallax" data-depth="6"></div>
            <div class="scene-ring b parallax" data-depth="11"></div>
            <div class="scene-ring c parallax" data-depth="14"></div>
            <div class="scene-buddha parallax" data-depth="7"></div>
            <div class="scene-floor"></div>
            {floating_markup}
          </div>
        </div>
        <div class="marquee" aria-hidden="true">
          <div class="marquee-track">{marquee_markup}</div>
        </div>
      </section>

      <section class="section reveal" id="programs">
        <div class="section-head">
          <div>
            <span class="eyebrow">Programs</span>
            <h2>Structured online yoga paths for different stages of life.</h2>
          </div>
          <p>
            Each path is designed to feel steady, intentional, and supportive, with live guidance and replay
            continuity built into the academy flow.
          </p>
        </div>
        <div class="grid two">{program_cards}</div>
      </section>

      <section class="section reveal" id="pricing">
        <div class="section-head">
          <div>
            <span class="eyebrow">Pricing hints</span>
            <h2>Clearer pricing before a learner commits.</h2>
          </div>
          <p>
            Families often want a trustworthy price range before they enquire. These pricing hints make the first decision calmer and more transparent.
          </p>
        </div>
        <div class="grid two">{pricing_markup}</div>
        <div class="cta-band">
          <h3>Need help choosing the right path before paying?</h3>
          <p>Book a free preview or demo conversation and we will help you choose the most suitable class rhythm first.</p>
          <div class="actions">
            <a class="button" href="{WHATSAPP_URL}">Book a free preview</a>
            <a class="button secondary" href="{LIVE_ZOOM_URL}">Join a live session</a>
          </div>
        </div>
      </section>

      <section class="section reveal">
        <div class="section-head">
          <div>
            <span class="eyebrow">Weekly rhythm</span>
            <h2>Live classes with replay support.</h2>
          </div>
          <p>
            The academy works like a calmer operating system for yoga learning: live sessions, support, and
            follow-through all move together.
          </p>
        </div>
        <div class="grid two">
          <div class="info-card reveal" style="--delay:0.08s;">
            <h3>Typical live rhythm</h3>
            <ul class="schedule-list">
              <li>Morning grounding classes during the week</li>
              <li>Evening flows for working parents and busy learners</li>
              <li>Kids yoga and certification sessions in specialty batches</li>
              <li>Replay support to help learners continue calmly</li>
            </ul>
          </div>
          <div class="info-card reveal" style="--delay:0.16s;">
            <h3>Why learners use the app</h3>
            <p>
              The academy app keeps admissions, learner accounts, class links, payment flow, and support
              follow-up in one place. That gives search visitors a clean next step after they find the site.
            </p>
            <div class="support-stack" style="margin-top:0.8rem;">
              <div class="support-pill">
                <strong>Admissions stay simple</strong>
                <span>Account, batch, and support in one place</span>
              </div>
              <div class="support-pill">
                <strong>Families stay connected</strong>
                <span>Live class access, replay, and follow-up stay calm</span>
              </div>
              <div class="actions">
                <a class="button" href="{academy_shell_url()}">Enter the app</a>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="section reveal" id="why-us">
        <div class="section-head">
          <div>
            <span class="eyebrow">Why us</span>
            <h2>Why the Matrika experience feels steadier than a typical class link.</h2>
          </div>
          <p>
            The academy is designed to reduce uncertainty for mothers, parents, and trainees by making the digital flow feel more human and more guided.
          </p>
        </div>
        <div class="grid three">{why_us_markup}</div>
      </section>

      <section class="section reveal" id="experience">
        <div class="section-head">
          <div>
            <span class="eyebrow">Learner experience</span>
            <h2>What families usually value after they begin.</h2>
          </div>
          <p>
            These are the qualities people tend to care about most once they join: slower guidance, replay continuity, and a clearer sense of support.
          </p>
        </div>
        <div class="grid three">{experience_markup}</div>
      </section>

      <section class="section reveal" id="journey">
        <div class="section-head">
          <div>
            <span class="eyebrow">Journey</span>
            <h2>A simple, modern flow from search to steady practice.</h2>
          </div>
          <p>
            The landing page inspires confidence first, then hands learners into the academy app for the
            deeper working experience.
          </p>
        </div>
        <div class="grid three">{ritual_cards}</div>
      </section>

      <section class="section reveal" id="leadership">
        <div class="section-head">
          <div>
            <span class="eyebrow">Instructor guidance</span>
            <h2>Led with teaching care, held together with digital clarity.</h2>
          </div>
          <p>
            Matrika is guided by a leadership team that keeps the academy feeling nurturing, practical, and trustworthy from the very first visit.
          </p>
        </div>
        <div class="grid two">
          <article class="info-card reveal" style="--delay:0.08s;">
            <span class="card-kicker">Managing Director</span>
            <h3>{esc(MD_NAME)}</h3>
            <p>
              Dr. Lavanya shapes the care-first teaching direction behind the academy, helping prenatal, postnatal, kids, and teacher-training journeys feel more grounded and intentional.
            </p>
          </article>
          <article class="info-card reveal" style="--delay:0.16s;">
            <span class="card-kicker">Chief Executive Officer</span>
            <h3>{esc(CEO_NAME)}</h3>
            <p>
              Abhinav guides the digital experience so admissions, class access, payments, and follow-through feel clearer, calmer, and easier for families to trust.
            </p>
          </article>
        </div>
      </section>

      <section class="section reveal" id="insights">
        <div class="section-head">
          <div>
            <span class="eyebrow">Deeper guides</span>
            <h2>Search-friendly pages for each major yoga path.</h2>
          </div>
          <p>
            These pages help Google and first-time visitors understand each program in more detail before they
            move into the academy app.
          </p>
        </div>
        <div class="grid two">{seo_cards}</div>
      </section>

      <section class="section reveal" id="faq">
        <div class="section-head">
          <div>
            <span class="eyebrow">Questions</span>
            <h2>Common questions about Matrika Yoga Academy.</h2>
          </div>
          <p>
            Clear answers help search visitors decide faster and move into the right program with confidence.
          </p>
        </div>
        <div class="grid faq-grid">{faq_markup}</div>
      </section>

      <section class="section reveal" id="contact">
        <div class="section-head">
          <div>
            <span class="eyebrow">Contact</span>
            <h2>Speak with the academy team.</h2>
          </div>
          <p>
            If someone is still choosing between tracks, the fastest path is to talk to the academy directly
            and then continue inside the app.
          </p>
        </div>
        <div class="contact-grid">
          <div class="contact-card reveal" style="--delay:0.08s;">
            <h3>Direct support</h3>
            <p>Email: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a><br />Phone: <a href="tel:{CONTACT_PHONE}">{CONTACT_PHONE}</a></p>
          </div>
          <div class="contact-card reveal" style="--delay:0.16s;">
            <h3>Quick actions</h3>
            <div class="actions">
              <a class="button" href="{academy_shell_url()}">Open academy app</a>
              <a class="button secondary" href="{WHATSAPP_URL}">WhatsApp the academy</a>
            </div>
            <div class="cta-band">
              <h3>Ready to begin?</h3>
              <p>Use the academy app for live classes, admissions, learner accounts, and the calm digital flow.</p>
            </div>
          </div>
          <div class="contact-card reveal" style="--delay:0.24s;">
            <h3>Leadership</h3>
            <p><strong>{esc(CEO_NAME)}</strong> · CEO<br /><strong>{esc(MD_NAME)}</strong> · Managing Director</p>
            <div class="cta-band">
              <h3>Care-first direction</h3>
              <p>The academy is led with both digital clarity and teaching care in mind, so learners know who is guiding the experience behind the scenes.</p>
            </div>
          </div>
        </div>
      </section>

      <p class="footer">
        Public website: {esc(site_host())} · Academy app: {esc(academy_shell_url())}
      </p>
    </main>
    <a class="floating-whatsapp" href="{WHATSAPP_URL}" target="_blank" rel="noopener noreferrer">WhatsApp the academy</a>
    <script>
      (() => {{
        const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        const progressBar = document.getElementById("scroll-progress-bar");
        const updateProgress = () => {{
          const scrollable = document.documentElement.scrollHeight - window.innerHeight;
          const ratio = scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0;
          progressBar.style.width = `${{Math.min(100, Math.max(0, ratio))}}%`;
        }};
        updateProgress();
        window.addEventListener("scroll", updateProgress, {{ passive: true }});
        window.addEventListener("resize", updateProgress);

        const revealItems = document.querySelectorAll(".reveal");
        if (!prefersReducedMotion && "IntersectionObserver" in window) {{
          const revealObserver = new IntersectionObserver(
            (entries) => {{
              entries.forEach((entry) => {{
                if (!entry.isIntersecting) return;
                entry.target.classList.add("is-visible");
                revealObserver.unobserve(entry.target);
              }});
            }},
            {{ threshold: 0.14, rootMargin: "0px 0px -8% 0px" }}
          );
          revealItems.forEach((item) => {{
            if (!item.classList.contains("reveal-visible")) {{
              revealObserver.observe(item);
            }}
          }});
        }} else {{
          revealItems.forEach((item) => item.classList.add("is-visible"));
        }}

        const heroScene = document.querySelector("[data-hero-scene]");
        if (heroScene && !prefersReducedMotion) {{
          const parallaxItems = heroScene.querySelectorAll("[data-depth]");
          heroScene.addEventListener("pointermove", (event) => {{
            const rect = heroScene.getBoundingClientRect();
            const offsetX = (event.clientX - rect.left) / rect.width - 0.5;
            const offsetY = (event.clientY - rect.top) / rect.height - 0.5;
            parallaxItems.forEach((item) => {{
              const depth = Number(item.dataset.depth || 8);
              const translateX = offsetX * depth;
              const translateY = offsetY * depth * -1;
              item.style.transform = `translate3d(${{translateX}}px, ${{translateY}}px, 0)`;
            }});
          }});
          heroScene.addEventListener("pointerleave", () => {{
            parallaxItems.forEach((item) => {{
              item.style.transform = "";
            }});
          }});
        }}

        if ("serviceWorker" in navigator) {{
          window.addEventListener("load", () => {{
            navigator.serviceWorker.register("{PUBLIC_SITE_URL}/sw.js").catch(() => {{}});
          }});
        }}
      }})();
    </script>
  </body>
</html>
"""


def seo_content_page_html(slug: str) -> str:
    page = SEO_CONTENT_PAGES[slug]
    bullet_markup = "".join(f"<li>{esc(point)}</li>" for point in page["points"])
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{esc(page["title"])}</title>
    <meta name="description" content="{esc(page["description"])}" />
    <link rel="canonical" href="{seo_page_url(slug)}" />
    <link rel="icon" href="{PUBLIC_SITE_URL}/assets/matrika_logo.svg" type="image/svg+xml" />
    <meta name="theme-color" content="#F7F0E8" />
    <link rel="manifest" href="{PUBLIC_SITE_URL}/manifest.webmanifest" />
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:wght@400;500;700;800&display=swap');
      :root {{
        --bg: #f7f0e8;
        --card: rgba(255, 250, 245, 0.84);
        --ink: #3d2b1f;
        --muted: #705c4d;
        --pista: #8fa876;
        --forest: #4a6741;
        --terracotta: #c4785a;
        --blush: #e8a882;
        --line: rgba(74, 103, 65, 0.13);
        --shadow: 0 20px 56px rgba(86, 58, 42, 0.1);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(196, 120, 90, 0.14), transparent 28%),
          linear-gradient(160deg, var(--bg), #fbf5ef 48%, #f0dfd2);
      }}
      .shell {{
        width: min(1080px, calc(100vw - 2rem));
        margin: 0 auto;
        padding: 1.2rem 0 3.5rem;
      }}
      .topbar,
      .hero,
      .section {{
        border-radius: 30px;
        border: 1px solid var(--line);
        background: var(--card);
        box-shadow: var(--shadow);
        backdrop-filter: blur(18px);
      }}
      .topbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        padding: 1rem 1.1rem;
      }}
      .brand {{
        display: inline-flex;
        align-items: center;
        gap: 0.85rem;
        color: inherit;
        text-decoration: none;
      }}
      .brand img {{
        width: 54px;
        height: 54px;
        border-radius: 16px;
      }}
      .brand strong {{
        display: block;
        font-family: "Cormorant Garamond", serif;
        font-size: 1.45rem;
        letter-spacing: -0.04em;
        color: var(--forest);
      }}
      .brand span {{
        color: var(--muted);
        font-size: 0.9rem;
      }}
      .actions {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }}
      .button {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.9rem 1.15rem;
        border-radius: 999px;
        text-decoration: none;
        font-weight: 700;
        background: linear-gradient(135deg, var(--terracotta), var(--blush));
        color: white;
      }}
      .button.secondary {{
        background: rgba(255,255,255,0.88);
        color: var(--ink);
        border: 1px solid var(--line);
      }}
      .hero {{
        margin-top: 1.1rem;
        padding: clamp(1.4rem, 4vw, 2.6rem);
        position: relative;
        overflow: hidden;
      }}
      .hero::after {{
        content: "";
        position: absolute;
        right: -1rem;
        bottom: -1rem;
        width: min(26vw, 240px);
        height: min(34vw, 320px);
        background: url("{PUBLIC_SITE_URL}/assets/buddha_meditation.svg") center bottom / contain no-repeat;
        opacity: 0.12;
      }}
      .eyebrow {{
        display: inline-flex;
        padding: 0.38rem 0.72rem;
        border-radius: 999px;
        background: rgba(143, 168, 118, 0.14);
        color: var(--forest);
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
      }}
      h1, h2, h3 {{
        font-family: "Cormorant Garamond", serif;
        letter-spacing: -0.05em;
      }}
      h1 {{
        margin: 0.7rem 0 0.8rem;
        font-size: clamp(2.5rem, 6vw, 4.4rem);
        line-height: 0.92;
        max-width: 10ch;
      }}
      .hero p,
      .section p,
      li {{
        color: var(--muted);
        line-height: 1.75;
      }}
      .hero-grid,
      .grid {{
        display: grid;
        gap: 1rem;
      }}
      .hero-grid {{
        grid-template-columns: minmax(0, 1.08fr) minmax(280px, 0.92fr);
        align-items: center;
      }}
      .story-card,
      .point-card {{
        padding: 1.05rem;
        border-radius: 24px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.74);
      }}
      .floating-whatsapp {{
        position: fixed;
        right: 1rem;
        bottom: 1rem;
        z-index: 20;
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.88rem 1rem;
        border-radius: 999px;
        text-decoration: none;
        color: #fff;
        background: linear-gradient(135deg, var(--forest), var(--pista));
        box-shadow: 0 18px 36px rgba(74, 103, 65, 0.24);
        font-size: 0.92rem;
        font-weight: 800;
      }}
      .floating-whatsapp::before {{
        content: "●";
        font-size: 0.74rem;
      }}
      .point-card ul {{
        margin: 0;
        padding-left: 1.1rem;
      }}
      .section {{
        margin-top: 1.1rem;
        padding: 1.25rem;
      }}
      @media (max-width: 900px) {{
        .topbar, .hero-grid {{
          display: grid;
          grid-template-columns: 1fr;
        }}
        h1 {{
          max-width: none;
        }}
      }}
    </style>
  </head>
  <body>
    <main class="shell">
      <header class="topbar">
        <a class="brand" href="{PUBLIC_SITE_URL}/">
          <img src="{PUBLIC_SITE_URL}/assets/matrika_logo.svg" alt="Matrika Yoga Academy logo" />
          <div>
            <strong>Matrika Yoga Academy</strong>
            <span>Calm online yoga paths with live and replay support</span>
          </div>
        </a>
        <nav class="actions">
          <a class="button" href="{academy_shell_url()}">Open Academy App</a>
          <a class="button secondary" href="{PUBLIC_SITE_URL}/">Back to website</a>
        </nav>
      </header>
      <section class="hero">
        <div class="hero-grid">
          <div>
            <span class="eyebrow">{esc(page["eyebrow"])}</span>
            <h1>{esc(page["headline"])}</h1>
            <p>{esc(page["intro"])}</p>
            <div class="actions" style="margin-top:1rem;">
              <a class="button" href="{academy_shell_url()}">Continue into the academy</a>
              <a class="button secondary" href="mailto:{CONTACT_EMAIL}">Email the team</a>
            </div>
          </div>
          <div class="point-card">
            <h3>What makes this path useful</h3>
            <ul>{bullet_markup}</ul>
          </div>
        </div>
      </section>
      <section class="section">
        <span class="eyebrow">Leadership</span>
        <h2>Guided by a calmer academy vision.</h2>
        <p>
          The academy experience is shaped by <strong>{esc(CEO_NAME)}</strong>, CEO, and <strong>{esc(MD_NAME)}</strong>, Managing Director,
          so the digital flow and teaching care move together.
        </p>
        <div class="actions" style="margin-top:1rem;">
          <a class="button" href="{WHATSAPP_URL}">Book a free preview</a>
          <a class="button secondary" href="mailto:{CONTACT_EMAIL}">Email the academy</a>
        </div>
      </section>
    </main>
    <a class="floating-whatsapp" href="{WHATSAPP_URL}" target="_blank" rel="noopener noreferrer">WhatsApp the academy</a>
    <script>
      if ("serviceWorker" in navigator) {{
        window.addEventListener("load", () => {{
          navigator.serviceWorker.register("{PUBLIC_SITE_URL}/sw.js").catch(() => {{}});
        }});
      }}
    </script>
  </body>
</html>
"""


async def wait_for_streamlit() -> None:
    health_url = f"{STREAMLIT_HTTP_BASE}{APP_BASE_PATH}/_stcore/health"
    async with httpx.AsyncClient(timeout=2.0) as client:
        for _ in range(60):
            try:
                response = await client.get(health_url)
                if response.status_code == 200:
                    return
            except Exception:
                pass
            await asyncio.sleep(1)
    raise RuntimeError("Streamlit did not become healthy in time.")


def start_streamlit_process() -> subprocess.Popen[str]:
    env = os.environ.copy()
    command = [
        "streamlit",
        "run",
        "app.py",
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(INTERNAL_STREAMLIT_PORT),
        "--server.headless",
        "true",
        "--server.baseUrlPath",
        APP_BASE_SEGMENT,
        "--server.fileWatcherType",
        "none",
        "--browser.gatherUsageStats",
        "false",
    ]
    return subprocess.Popen(
        command,
        cwd=str(APP_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global streamlit_process
    streamlit_process = start_streamlit_process()
    await wait_for_streamlit()
    try:
        yield
    finally:
        if streamlit_process and streamlit_process.poll() is None:
            streamlit_process.terminate()
            with contextlib.suppress(Exception):
                streamlit_process.wait(timeout=8)
        streamlit_process = None


app = FastAPI(lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def landing_page() -> HTMLResponse:
    return HTMLResponse(landing_page_html())


@app.get("/prenatal-yoga", response_class=HTMLResponse)
async def prenatal_yoga_page() -> HTMLResponse:
    return HTMLResponse(seo_content_page_html("prenatal-yoga"))


@app.get("/postnatal-yoga", response_class=HTMLResponse)
async def postnatal_yoga_page() -> HTMLResponse:
    return HTMLResponse(seo_content_page_html("postnatal-yoga"))


@app.get("/kids-yoga-classes", response_class=HTMLResponse)
async def kids_yoga_page() -> HTMLResponse:
    return HTMLResponse(seo_content_page_html("kids-yoga-classes"))


@app.get("/yoga-teacher-training", response_class=HTMLResponse)
async def teacher_training_page() -> HTMLResponse:
    return HTMLResponse(seo_content_page_html("yoga-teacher-training"))


@app.get("/academy", response_class=HTMLResponse)
async def academy_shell() -> HTMLResponse:
    return HTMLResponse(academy_shell_html(), headers={"x-robots-tag": "noindex, nofollow"})


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt() -> str:
    return "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            f"Disallow: {APP_BASE_PATH}/",
            f"Sitemap: {PUBLIC_SITE_URL}/sitemap.xml",
        ]
    )


@app.get("/sitemap.xml")
async def sitemap_xml() -> Response:
    page_entries = "\n".join(
        f"""  <url>
    <loc>{seo_page_url(slug)}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>"""
        for slug in SEO_CONTENT_PAGES
    )
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{PUBLIC_SITE_URL}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
{page_entries}
</urlset>
"""
    return Response(content=body, media_type="application/xml")


@app.get("/manifest.webmanifest")
async def manifest() -> Response:
    body = {
        "name": "Matrika Yoga Academy",
        "short_name": "Matrika",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#F7F0E8",
        "theme_color": "#C4785A",
        "description": "Online prenatal yoga, postnatal recovery, kids yoga, and teacher training.",
        "icons": [
            {
                "src": f"{PUBLIC_SITE_URL}/assets/matrika_logo.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any",
            }
        ],
    }
    return Response(content=json.dumps(body), media_type="application/manifest+json")


@app.get("/sw.js")
async def service_worker() -> Response:
    pre_cache = [
        "/",
        "/academy",
        "/robots.txt",
        "/sitemap.xml",
        "/assets/matrika_logo.svg",
        "/assets/buddha_meditation.svg",
    ] + [f"/{slug}" for slug in SEO_CONTENT_PAGES]
    script = f"""
const CACHE_NAME = "matrika-static-v3";
const PRECACHE_URLS = {json.dumps(pre_cache)};

self.addEventListener("install", (event) => {{
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS)));
  self.skipWaiting();
}});

self.addEventListener("activate", (event) => {{
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
}});

self.addEventListener("fetch", (event) => {{
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    fetch(request)
      .then((response) => {{
        const cloned = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, cloned));
        return response;
      }})
      .catch(() => caches.match(request).then((cached) => cached || caches.match("/")))
  );
}});
"""
    return Response(content=script, media_type="application/javascript")


@app.get("/assets/matrika_logo.svg")
async def logo_asset() -> FileResponse:
    return FileResponse(LOGO_PATH, media_type="image/svg+xml")


@app.get("/assets/buddha_meditation.svg")
async def buddha_asset() -> FileResponse:
    return FileResponse(BUDDHA_PATH, media_type="image/svg+xml")


def upstream_url(path: str, query: str) -> str:
    normalized_path = path or "/"
    base = f"{STREAMLIT_HTTP_BASE}{APP_BASE_PATH}{normalized_path}"
    return f"{base}?{query}" if query else base


@app.get(APP_BASE_PATH)
async def academy_app_redirect() -> RedirectResponse:
    return RedirectResponse(url="/academy", status_code=307)


@app.api_route(f"{APP_BASE_PATH}" + "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_streamlit(path: str, request: Request) -> Response:
    normalized_path = path.strip("/")
    if request.method == "GET" and not normalized_path and request.query_params.get("academy_embed") != "1":
        return RedirectResponse(url="/academy", status_code=307)

    body = await request.body()
    headers = {key: value for key, value in request.headers.items() if key.lower() != "host"}
    target = upstream_url(f"/{path}", request.url.query)

    async with httpx.AsyncClient(follow_redirects=False, timeout=60.0) as client:
        upstream = await client.request(request.method, target, headers=headers, content=body)

    excluded = {"content-encoding", "transfer-encoding", "connection", "keep-alive"}
    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in excluded
    }
    response_headers["x-robots-tag"] = "noindex, nofollow"
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
    )


@app.websocket(f"{APP_BASE_PATH}/_stcore/stream")
async def proxy_streamlit_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    query = websocket.url.query
    upstream = f"{STREAMLIT_WS_BASE}{APP_BASE_PATH}/_stcore/stream"
    if query:
        upstream = f"{upstream}?{query}"

    extra_headers = []
    if cookie := websocket.headers.get("cookie"):
        extra_headers.append(("cookie", cookie))

    try:
        async with websockets.connect(upstream, additional_headers=extra_headers, open_timeout=30) as upstream_ws:
            async def client_to_upstream() -> None:
                while True:
                    message = await websocket.receive()
                    message_type = message.get("type")
                    if message_type == "websocket.disconnect":
                        break
                    if message.get("text") is not None:
                        await upstream_ws.send(message["text"])
                    elif message.get("bytes") is not None:
                        await upstream_ws.send(message["bytes"])

            async def upstream_to_client() -> None:
                async for message in upstream_ws:
                    if isinstance(message, bytes):
                        await websocket.send_bytes(message)
                    else:
                        await websocket.send_text(message)

            await asyncio.gather(client_to_upstream(), upstream_to_client())
    except Exception:
        with contextlib.suppress(Exception):
            await websocket.close()
