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
LIVE_ZOOM_URL = "https://us04web.zoom.us/j/8048675666?pwd=KF3fzQ5y1ZaDibDafMrbWHyCHl2jqV.1"
WHATSAPP_URL = f"https://wa.me/917893939545?text={quote('Hi Matrika Academy, I want help choosing the right yoga path.')}"

PROGRAMS = [
    ("Garbhasanskara Flow", "Gentle breath, grounding, and pregnancy-aware movement with live and replay support."),
    ("Prenatal + Postnatal Care", "Recovery-aware sessions designed for comfort, healing rhythm, and steadier routine building."),
    ("Kids Yoga Studio", "Playful movement, stories, balance work, and calmer focus for children."),
    ("Teacher Certification", "Mentored training with sequencing, practicum, and supportive feedback."),
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
]

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
    <style>
      :root {{
        --bg: #f5f8ef;
        --bg-soft: #e4eed9;
        --ink: #203629;
        --muted: #5f7666;
        --pista: #a7c97a;
        --forest: #4c6d3f;
        --line: rgba(76, 109, 63, 0.14);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(167, 201, 122, 0.20), transparent 32%),
          linear-gradient(160deg, var(--bg), #fbfff6 48%, var(--bg-soft));
      }}
      .loader {{
        position: fixed;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
        background: rgba(245, 248, 239, 0.96);
        z-index: 20;
        transition: opacity .35s ease, visibility .35s ease;
      }}
      .loader.hidden {{
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
      }}
      .card {{
        width: min(92vw, 460px);
        border-radius: 28px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.8);
        padding: 1.4rem;
        text-align: center;
        box-shadow: 0 24px 60px rgba(60,92,47,0.14);
      }}
      .card img {{
        width: 72px;
        height: 72px;
        border-radius: 22px;
      }}
      .spinner {{
        width: 60px;
        height: 60px;
        margin: 1rem auto 0;
        border-radius: 999px;
        border: 5px solid rgba(167, 201, 122, 0.22);
        border-top-color: var(--forest);
        animation: spin .9s linear infinite;
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
        padding: 0.8rem 1rem;
        border-radius: 999px;
        text-decoration: none;
        color: var(--ink);
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.75);
      }}
      @keyframes spin {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
      }}
    </style>
  </head>
  <body>
    <div class="loader" id="loader">
      <div class="card">
        <img src="{PUBLIC_SITE_URL}/assets/matrika_logo.svg" alt="Matrika Academy logo" />
        <h1>Opening Matrika Academy</h1>
        <p class="copy">
          The academy space is loading. We are keeping the experience calm and branded here so you do not have
          to wait on the default Streamlit skeleton screen.
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
      }}, 2200);
      if (frame) {{
        frame.addEventListener('load', function () {{
          window.setTimeout(function () {{
            frameReady = true;
            maybeHideLoader();
          }}, 1200);
        }});
      }}
      window.setTimeout(function () {{
        if (loader) {{
          loader.querySelector('.copy').textContent =
            'The academy is still warming up. This can happen on the free hosting plan after inactivity, but the app should appear shortly.';
        }}
      }}, 8000);
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
          <strong data-count="{value}" data-suffix="{suffix}">0{esc(suffix)}</strong>
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
      :root {{
        --bg: #f6f9f1;
        --bg-soft: #edf4e3;
        --card: rgba(253, 255, 250, 0.82);
        --card-strong: rgba(255, 255, 255, 0.9);
        --ink: #142717;
        --muted: #607261;
        --pista: #adc87b;
        --pista-bright: #c7e394;
        --forest: #496441;
        --moss: #24412d;
        --line: rgba(73, 100, 65, 0.14);
        --line-strong: rgba(73, 100, 65, 0.22);
        --shadow: 0 28px 90px rgba(72, 99, 56, 0.12);
        --shadow-soft: 0 12px 34px rgba(72, 99, 56, 0.08);
        --max-width: min(1220px, calc(100vw - 2rem));
      }}
      * {{ box-sizing: border-box; }}
      html {{ scroll-behavior: smooth; }}
      body {{
        margin: 0;
        font-family: "SF Pro Text", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at 12% 10%, rgba(173, 200, 123, 0.28), transparent 28%),
          radial-gradient(circle at 88% 6%, rgba(132, 181, 114, 0.16), transparent 24%),
          linear-gradient(160deg, var(--bg), #fbfff8 48%, var(--bg-soft));
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
        background: rgba(192, 225, 141, 0.3);
        animation: matrika-orb-drift 18s ease-in-out infinite;
      }}
      body::after {{
        width: 30vw;
        height: 30vw;
        right: -8vw;
        bottom: -8vw;
        background: rgba(125, 175, 118, 0.22);
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
        background: rgba(177, 214, 121, 0.18);
        animation: matrika-aura-float 19s ease-in-out infinite;
      }}
      .ambient-orb::after {{
        width: 18rem;
        height: 18rem;
        left: -4rem;
        bottom: 14%;
        background: rgba(128, 163, 111, 0.14);
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
        border: 1px solid rgba(255, 255, 255, 0.7);
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.7);
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
        font-size: 1.35rem;
        letter-spacing: -0.04em;
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
        background: linear-gradient(135deg, var(--pista), #7ea55f);
        color: #fff;
        text-decoration: none;
        font-weight: 700;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 16px 34px rgba(76, 109, 63, 0.18);
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
        box-shadow: 0 22px 42px rgba(76, 109, 63, 0.22);
      }}
      .button.secondary {{
        background: rgba(255,255,255,0.78);
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
          radial-gradient(circle at 18% 16%, rgba(206, 236, 149, 0.28), transparent 26%),
          radial-gradient(circle at 82% 18%, rgba(164, 196, 123, 0.2), transparent 22%),
          linear-gradient(145deg, rgba(251, 255, 246, 0.94), rgba(229, 239, 213, 0.82));
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
        background: rgba(167, 201, 122, 0.18);
        color: var(--forest);
        text-transform: uppercase;
        letter-spacing: 0.13em;
        font-size: 0.72rem;
        font-weight: 800;
      }}
      h1 {{
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
          radial-gradient(circle at 48% 34%, rgba(210, 234, 171, 0.54), transparent 34%),
          linear-gradient(180deg, rgba(255, 255, 255, 0.62), rgba(233, 242, 220, 0.54));
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
        background: radial-gradient(circle, rgba(182, 215, 132, 0.42), rgba(182, 215, 132, 0.14) 46%, transparent 72%);
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
        background: rgba(173, 200, 123, 0.14);
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
      .faq-item,
      .journey-card,
      .contact-card {{
        padding: 1.2rem;
        border-radius: 24px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.72);
        box-shadow: var(--shadow-soft);
        transition: transform 0.4s ease, border-color 0.35s ease, box-shadow 0.35s ease, background 0.35s ease;
      }}
      .program-card:hover,
      .info-card:hover,
      .journey-card:hover,
      .contact-card:hover {{
        transform: translateY(-8px);
        border-color: var(--line-strong);
        background: rgba(255,255,255,0.86);
        box-shadow: 0 22px 48px rgba(72, 99, 56, 0.12);
      }}
      .program-card h3,
      .info-card h3,
      .journey-card h3,
      .contact-card h3 {{
        margin: 0 0 0.45rem;
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
        background: rgba(173, 200, 123, 0.16);
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
      .journey-card p {{
        margin-bottom: 0;
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
        grid-template-columns: minmax(0, 0.94fr) minmax(0, 1.06fr);
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
          linear-gradient(135deg, rgba(173, 200, 123, 0.2), rgba(237, 244, 227, 0.9));
        border: 1px solid rgba(173, 200, 123, 0.28);
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
        .hero-stat-grid {{
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
          <a href="#journey">Journey</a>
          <a href="#faq">FAQ</a>
          <a href="#contact">Contact</a>
        </nav>
        <nav class="actions" aria-label="Primary">
          <a class="button" href="{academy_shell_url()}">Open Academy App</a>
          <a class="button secondary" href="{LIVE_ZOOM_URL}">Join Live Class</a>
        </nav>
      </header>

      <section class="hero reveal reveal-visible">
        <div class="hero-grid">
          <div class="hero-copy">
            <span class="eyebrow">Yoga academy in one calm place</span>
            <h1>Matrika Yoga Academy supports breath, growth, and steady practice.</h1>
            <p>
              Explore online prenatal yoga, postnatal recovery guidance, kids yoga classes, and yoga teacher
              training from a calmer, more guided digital experience. Families and learners can start on the
              website and continue into the full academy app when they are ready.
            </p>
            <div class="actions">
              <a class="button" href="{academy_shell_url()}">Start with the academy app</a>
              <a class="button secondary" href="mailto:{CONTACT_EMAIL}">Email the academy</a>
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
        </div>
      </section>

      <p class="footer">
        Public website: {esc(site_host())} · Academy app: {esc(academy_shell_url())}
      </p>
    </main>
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

        const counters = document.querySelectorAll("[data-count]");
        const counterObserver = !prefersReducedMotion && "IntersectionObserver" in window
          ? new IntersectionObserver((entries) => {{
              entries.forEach((entry) => {{
                if (!entry.isIntersecting || entry.target.dataset.started === "1") return;
                entry.target.dataset.started = "1";
                const target = Number(entry.target.dataset.count || "0");
                const suffix = entry.target.dataset.suffix || "";
                const duration = 1400;
                const startTime = performance.now();
                const tick = (now) => {{
                  const progress = Math.min(1, (now - startTime) / duration);
                  const eased = 1 - Math.pow(1 - progress, 3);
                  entry.target.textContent = `${{Math.round(target * eased)}}${{suffix}}`;
                  if (progress < 1) {{
                    requestAnimationFrame(tick);
                  }}
                }};
                requestAnimationFrame(tick);
                counterObserver.unobserve(entry.target);
              }});
            }}, {{ threshold: 0.45 }})
          : null;
        counters.forEach((counter) => {{
          if (counterObserver) {{
            counterObserver.observe(counter);
          }} else {{
            counter.textContent = `${{counter.dataset.count || "0"}}${{counter.dataset.suffix || ""}}`;
          }}
        }});
      }})();
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
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{PUBLIC_SITE_URL}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    return Response(content=body, media_type="application/xml")


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
