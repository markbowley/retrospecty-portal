import hmac
import json
import os
import re
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED = os.getenv("ALLOWED_CHAT_ID")
API = f"https://api.telegram.org/bot{TOKEN}"
APP_NAME = os.getenv("BRAND_NAME", "Retrospecty")
DOMAIN_NAME = os.getenv("BRAND_DOMAIN", "retrospecty.com")
HERE = Path(__file__).parent

# Design lives in plain files: templates/*.html for markup, static/style.css for styles.
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
templates = Jinja2Templates(directory=HERE / "templates")  # escapes all text by default

# Mo, running elsewhere, collects submissions from here every minute using this
# shared secret. Submissions only wait on this server until he has them.
INTAKE_SECRET = os.getenv("INTAKE_SECRET", "")
SUBMISSIONS = HERE / "submissions"
MAX_WAITING = 200  # stop a flood of junk filling the disk

# The page copy lives in content.json and the sample report in sample_report.md.
# Mo, the agent, writes both (after approval). These defaults show until he does.
DEFAULTS = {
    "badge": "Engineered for Founders & Investors",
    "headline": "Stress-test your startup thesis before spending a single dollar.",
    "subhead": "Submit your product thesis or concept. Retrospecty compares it against "
               "real companies that failed with a similar model.",
    "features": [
        {"title": "1. Real failed companies", "body": "Your model is compared with named companies that shut down doing something similar."},
        {"title": "2. A source for every case", "body": "Each comparison links to a public source you can check yourself."},
        {"title": "3. Sent to your inbox", "body": "A clear breakdown of the main risks and what to do about them."},
    ],
    "form_heading": "Request an audit",
    "form_note": "Confidential and automated.",
    "cta_label": "Run audit →",
    "price_label": "",
    "sample_link_label": "See a sample report",
    "sample_intro": "A real report, produced by the same process yours will be.",
    "email_label": "Work Email",
    "thesis_label": "Startup idea",
    "thesis_placeholder": "Describe your product value prop, target audience, pricing model, and distribution channel.",
    "thanks_note": "A free preview of your report will be emailed to you, usually within ten minutes.",
}

def load_content() -> dict:
    """content.json over the defaults. A broken or missing file never breaks the page."""
    content = dict(DEFAULTS)
    try:
        data = json.loads((HERE / "content.json").read_text())
        for key, default in DEFAULTS.items():
            value = data.get(key)
            if key == "features":
                if (isinstance(value, list) and len(value) == 3
                        and all(isinstance(f, dict) and isinstance(f.get("title"), str)
                                and isinstance(f.get("body"), str) for f in value)):
                    content[key] = value
            elif isinstance(value, str):
                content[key] = value
    except (OSError, ValueError, AttributeError):
        pass
    return content


def sample_markdown() -> str:
    try:
        return (HERE / "sample_report.md").read_text()
    except OSError:
        return ""


def render(request: Request, name: str, title: str, status: int = 200, **context) -> HTMLResponse:
    """Render a template. The ?v= on the stylesheet changes whenever style.css does,
    so browsers pick up CSS edits straight away."""
    css_version = int((HERE / "static" / "style.css").stat().st_mtime)
    return templates.TemplateResponse(
        request, name,
        {"title": title, "app_name": APP_NAME, "css_version": css_version, **context},
        status_code=status,
    )


def card(request: Request, title: str, heading: str, message: str,
         email: str | None = None, status: int = 200) -> HTMLResponse:
    return render(request, "card.html", f"{title} — {APP_NAME}", status,
                  heading=heading, message=message, email=email)


def notify(text):
    """Plain text on purpose: a thesis full of symbols must not break delivery."""
    if ALLOWED and TOKEN:
        try:
            requests.post(f"{API}/sendMessage", json={"chat_id": ALLOWED, "text": text[:4000]}, timeout=10)
        except Exception as err:
            print(f"Telegram notification error: {err}")


@app.get("/", response_class=HTMLResponse)
def landing_page(request: Request):
    return render(request, "home.html", f"{APP_NAME} — Startup pre-mortem reports",
                  c=load_content(), has_sample=bool(sample_markdown().strip()))


@app.get("/sample", response_class=HTMLResponse)
def sample_report(request: Request):
    import markdown

    source = sample_markdown()
    if not source.strip():
        return card(request, "Sample report", "No sample yet", "Check back soon.", status=404)
    # Escape first so nothing in the report can inject HTML, then render the Markdown.
    rendered = markdown.markdown(source.replace("&", "&amp;").replace("<", "&lt;"), extensions=["extra"])
    rendered = rendered.replace('<a href="javascript:', '<a href="#')
    return render(request, "sample.html", f"Sample report — {APP_NAME}", report_html=rendered)


@app.post("/submit", response_class=HTMLResponse)
def handle_submission(request: Request, founder_email: str = Form(...), thesis: str = Form(...),
                      website: str = Form("")):
    founder_email, thesis = founder_email.strip(), thesis.strip()

    def thanks():
        return card(request, "Idea received", "Idea received",
                    f"Thanks. {load_content()['thanks_note']}", email=founder_email)

    if website.strip():          # only bots fill the hidden field; tell them nothing
        return thanks()
    if (len(thesis) < 40 or len(thesis) > 6000 or len(founder_email) > 254
            or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", founder_email)):
        return card(request, "Check your details", "Please check your details",
                    "We need a valid email address and a description of 40 to 6,000 characters.", status=400)

    SUBMISSIONS.mkdir(exist_ok=True)
    if len(list(SUBMISSIONS.glob("*.json"))) >= MAX_WAITING:
        return card(request, "Busy", "We are very busy", "Please try again in a few minutes.", status=503)
    sid = uuid.uuid4().hex
    (SUBMISSIONS / f"{sid}.json").write_text(json.dumps(
        {"id": sid, "email": founder_email, "thesis": thesis, "ts": time.time()}))
    notify("New idea submitted on the site. Mo will collect it.")
    return thanks()


@app.get("/paid", response_class=HTMLResponse)
def paid(request: Request):
    return card(request, "Thank you", "Payment received",
                "Thank you. Your full report will arrive by email within a few minutes.")


# --- collection API for Mo ----------------------------------------------------

def _check(secret: str | None) -> None:
    if not INTAKE_SECRET:
        raise HTTPException(503, "Intake is not configured.")
    if not secret or not hmac.compare_digest(secret, INTAKE_SECRET):
        raise HTTPException(401, "Not authorised.")


class Ack(BaseModel):
    ids: list[str]


@app.get("/api/submissions")
def list_submissions(x_intake_secret: str | None = Header(default=None)):
    _check(x_intake_secret)
    out = []
    for path in sorted(SUBMISSIONS.glob("*.json"), key=lambda p: p.stat().st_mtime)[:20]:
        try:
            out.append(json.loads(path.read_text()))
        except (OSError, ValueError):
            continue
    return {"submissions": out}


@app.post("/api/submissions/ack")
def ack_submissions(ack: Ack, x_intake_secret: str | None = Header(default=None)):
    _check(x_intake_secret)
    removed = 0
    for sid in ack.ids:
        if re.fullmatch(r"[0-9a-f]{32}", sid):        # never build a path from anything else
            try:
                (SUBMISSIONS / f"{sid}.json").unlink()
                removed += 1
            except OSError:
                pass
    return {"removed": removed}


# --- legal pages: plain HTML in templates/ -------------------------------------

@app.get("/privacy", response_class=HTMLResponse)
def privacy_policy():
    return HTMLResponse((HERE / "templates" / "privacy.html").read_text())


@app.get("/terms", response_class=HTMLResponse)
def terms_of_service():
    return HTMLResponse((HERE / "templates" / "terms.html").read_text())


@app.get("/data-protection", response_class=HTMLResponse)
def data_protection():
    return HTMLResponse((HERE / "templates" / "data-protection.html").read_text())
