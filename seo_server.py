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
    return f"{PUBLIC_SITE_URL}{APP_BASE_PATH}"


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
                "target": f"{academy_app_url()}",
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


def landing_page_html() -> str:
    program_cards = "".join(
        f"""
        <article class="program-card">
            <h3>{esc(title)}</h3>
            <p>{esc(body)}</p>
        </article>
        """
        for title, body in PROGRAMS
    )
    faq_markup = "".join(
        f"""
        <details class="faq-item">
            <summary>{esc(question)}</summary>
            <p>{esc(answer)}</p>
        </details>
        """
        for question, answer in FAQS
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
        --bg: #f5f8ef;
        --bg-soft: #e4eed9;
        --card: rgba(252, 255, 247, 0.94);
        --ink: #203629;
        --muted: #5f7666;
        --pista: #a7c97a;
        --forest: #4c6d3f;
        --moss: #33512f;
        --line: rgba(76, 109, 63, 0.14);
        --shadow: 0 22px 54px rgba(60, 92, 47, 0.14);
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
      .shell {{
        width: min(1120px, calc(100vw - 2rem));
        margin: 0 auto;
        padding: 1.25rem 0 3rem;
      }}
      .topbar {{
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: center;
        padding: 0.95rem 1.1rem;
        border: 1px solid var(--line);
        border-radius: 24px;
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(10px);
        box-shadow: var(--shadow);
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
      }}
      .brand strong {{
        display: block;
        font-size: 1.6rem;
      }}
      .brand span {{
        color: var(--muted);
        font-size: 0.95rem;
      }}
      .actions {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.7rem;
      }}
      .button {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.85rem 1.15rem;
        border-radius: 999px;
        background: linear-gradient(135deg, var(--pista), #7ea55f);
        color: #fff;
        text-decoration: none;
        font-weight: 700;
        box-shadow: 0 14px 28px rgba(76, 109, 63, 0.18);
      }}
      .button.secondary {{
        background: rgba(255,255,255,0.78);
        color: var(--ink);
        border: 1px solid var(--line);
        box-shadow: none;
      }}
      .hero {{
        margin-top: 1.25rem;
        padding: clamp(1.5rem, 4vw, 3rem);
        border-radius: 32px;
        position: relative;
        overflow: hidden;
        background: linear-gradient(145deg, rgba(251, 255, 245, 0.95), rgba(229, 239, 213, 0.88));
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
      }}
      .hero::after {{
        content: "";
        position: absolute;
        right: -2rem;
        bottom: -2rem;
        width: min(28vw, 280px);
        height: min(38vw, 380px);
        background: url("{PUBLIC_SITE_URL}/assets/buddha_meditation.svg") center bottom / contain no-repeat;
        opacity: 0.18;
        pointer-events: none;
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
        max-width: 11ch;
      }}
      .hero p {{
        max-width: 62ch;
        font-size: 1.05rem;
        line-height: 1.75;
        color: var(--muted);
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
      .section {{
        margin-top: 1.4rem;
        padding: 1.35rem;
        border-radius: 28px;
        background: var(--card);
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
      }}
      .section h2 {{
        margin: 0.5rem 0 0.3rem;
        font-size: clamp(1.6rem, 3.4vw, 2.6rem);
      }}
      .section p {{
        color: var(--muted);
        line-height: 1.7;
      }}
      .program-card, .info-card, .faq-item {{
        padding: 1.15rem;
        border-radius: 22px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.7);
      }}
      .program-card h3, .info-card h3 {{
        margin: 0 0 0.45rem;
      }}
      .schedule-list {{
        margin: 0;
        padding-left: 1.15rem;
        color: var(--muted);
        line-height: 1.8;
      }}
      summary {{
        cursor: pointer;
        font-weight: 700;
      }}
      .footer {{
        margin-top: 1.25rem;
        text-align: center;
        color: var(--muted);
        font-size: 0.95rem;
      }}
      @media (max-width: 900px) {{
        .topbar, .grid.two, .grid.three {{ grid-template-columns: 1fr; display: grid; }}
        .actions {{ justify-content: flex-start; }}
        .hero::after {{ opacity: 0.12; width: 180px; height: 240px; }}
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
            <span>Online prenatal yoga, kids yoga, and teacher training</span>
          </div>
        </a>
        <nav class="actions" aria-label="Primary">
          <a class="button" href="{academy_app_url()}">Open Academy App</a>
          <a class="button secondary" href="{LIVE_ZOOM_URL}">Join Live Class</a>
        </nav>
      </header>

      <section class="hero">
        <span class="eyebrow">Yoga academy in one calm place</span>
        <h1>Matrika Yoga Academy supports breath, growth, and steady practice.</h1>
        <p>
          Explore online prenatal yoga, postnatal recovery guidance, kids yoga classes, and yoga teacher
          training from a calmer, more guided digital experience. Families and learners can start on the
          website and continue into the full academy app when they are ready.
        </p>
        <div class="actions" style="margin-top:1rem;">
          <a class="button" href="{academy_app_url()}">Start with the academy app</a>
          <a class="button secondary" href="mailto:{CONTACT_EMAIL}">Email the academy</a>
          <a class="button secondary" href="tel:{CONTACT_PHONE}">Call {CONTACT_PHONE}</a>
        </div>
      </section>

      <section class="section">
        <span class="eyebrow">Programs</span>
        <h2>Structured online yoga paths for different stages of life.</h2>
        <div class="grid two">{program_cards}</div>
      </section>

      <section class="section">
        <span class="eyebrow">Weekly rhythm</span>
        <h2>Live classes with replay support.</h2>
        <div class="grid two">
          <div class="info-card">
            <h3>Typical live rhythm</h3>
            <ul class="schedule-list">
              <li>Morning grounding classes during the week</li>
              <li>Evening flows for working parents and busy learners</li>
              <li>Kids yoga and certification sessions in specialty batches</li>
              <li>Replay support to help learners continue calmly</li>
            </ul>
          </div>
          <div class="info-card">
            <h3>Why learners use the app</h3>
            <p>
              The academy app keeps admissions, learner accounts, class links, payment flow, and support
              follow-up in one place. That gives search visitors a clean next step after they find the site.
            </p>
            <div class="actions" style="margin-top:0.8rem;">
              <a class="button" href="{academy_app_url()}">Enter the app</a>
            </div>
          </div>
        </div>
      </section>

      <section class="section">
        <span class="eyebrow">Questions</span>
        <h2>Common questions about Matrika Yoga Academy.</h2>
        <div class="grid">{faq_markup}</div>
      </section>

      <section class="section">
        <span class="eyebrow">Contact</span>
        <h2>Speak with the academy team.</h2>
        <div class="grid two">
          <div class="info-card">
            <h3>Direct support</h3>
            <p>Email: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a><br />Phone: <a href="tel:{CONTACT_PHONE}">{CONTACT_PHONE}</a></p>
          </div>
          <div class="info-card">
            <h3>Quick actions</h3>
            <div class="actions">
              <a class="button" href="{academy_app_url()}">Open academy app</a>
              <a class="button secondary" href="{WHATSAPP_URL}">WhatsApp the academy</a>
            </div>
          </div>
        </div>
      </section>

      <p class="footer">
        Public website: {esc(site_host())} · Academy app: {esc(academy_app_url())}
      </p>
    </main>
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
    return RedirectResponse(url=f"{APP_BASE_PATH}/", status_code=307)


@app.api_route(f"{APP_BASE_PATH}" + "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_streamlit(path: str, request: Request) -> Response:
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
