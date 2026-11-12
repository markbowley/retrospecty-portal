import html
import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
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
}

CSS = """
            :root {
                --bg: #0b0f19;
                --card-bg: #111827;
                --border: #1f2937;
                --accent: #38bdf8;
                --accent-hover: #0284c7;
                --text-main: #f3f4f6;
                --text-muted: #9ca3af;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text-main); line-height: 1.6; padding: 0; display: flex; flex-direction: column; min-height: 100vh; }
            header { padding: 24px 40px; display: flex; justify-content: space-between; align-items: center; max-width: 1100px; width: 100%; margin: 0 auto; }
            .logo { font-weight: 700; font-size: 18px; letter-spacing: -0.5px; color: var(--text-main); }
            .logo span { color: var(--accent); }
            .hero { max-width: 900px; margin: 60px auto 40px auto; padding: 0 20px; text-align: center; }
            .badge { background: rgba(56, 189, 248, 0.1); color: var(--accent); border: 1px solid rgba(56, 189, 248, 0.2); font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; padding: 5px 14px 3px; border-radius: 20px; display: inline-block; margin-bottom: 20px; }
            h1 { font-size: 42px; font-weight: 800; letter-spacing: -1px; line-height: 1.15; margin-bottom: 16px; color: #ffffff; }
            .hero-sub { font-size: 18px; color: var(--text-muted); max-width: 680px; margin: 0 auto 40px auto; }
            
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; max-width: 1000px; margin: 0 auto 60px auto; padding: 0 20px; text-align: left; }
            @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
            
            .features { display: flex; flex-direction: column; gap: 24px; justify-content: center; }
            .feature-card { background: var(--card-bg); border: 1px solid var(--border); padding: 20px; border-radius: 8px; }
            .feature-card h3 { font-size: 16px; margin-bottom: 6px; color: var(--accent); }
            .feature-card p { font-size: 14px; color: var(--text-muted); margin: 0; }
            
            .form-container { background: var(--card-bg); border: 1px solid var(--border); padding: 32px; border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }
            .form-container h2 { font-size: 20px; margin-bottom: 8px; }
            .form-container p { font-size: 13px; color: var(--text-muted); margin-bottom: 24px; }
            label { display: block; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; color: var(--text-muted); }
            input, textarea { width: 100%; padding: 12px 14px; background: #0b0f19; border: 1px solid var(--border); border-radius: 6px; color: var(--text-main); font-size: 14px; margin-bottom: 20px; font-family: inherit; }
            input:focus, textarea:focus { outline: none; border-color: var(--accent); }
            textarea { height: 110px; resize: vertical; }
            button { background: var(--accent); color: #0b0f19; border: none; padding: 14px 24px; font-size: 14px; font-weight: 700; border-radius: 6px; cursor: pointer; width: 100%; transition: all 0.2s; }
            button:hover { background: var(--accent-hover); color: white; }
            
            footer { margin-top: auto; border-top: 1px solid var(--border); padding: 30px 40px; font-size: 12px; color: var(--text-muted); text-align: center; }
            .footer-links { margin-bottom: 12px; }
            .footer-links a { color: var(--text-muted); text-decoration: none; margin: 0 10px; }
            .footer-links a:hover { color: var(--text-main); }
            .price { font-size: 13px; color: var(--text-main); text-align: center; margin-top: 14px; }
            .sample-link { display: block; text-align: center; margin-top: 10px; font-size: 13px; color: var(--accent); text-decoration: none; }
            .sample-link:hover { text-decoration: underline; }
            .report { max-width: 720px; margin: 0 auto 60px auto; padding: 36px; background: #ffffff; color: #1a1a1a; border-radius: 12px; font-family: Georgia, "Times New Roman", serif; font-size: 16px; line-height: 1.6; }
            .report h1 { font-size: 28px; color: #111; margin-bottom: 8px; letter-spacing: 0; }
            .report h2 { font-size: 21px; margin: 32px 0 10px; color: #111; }
            .report h3 { font-size: 17px; margin: 24px 0 8px; color: #111; }
            .report p, .report ul { margin-bottom: 14px; }
            .report ul { padding-left: 22px; }
            .report a { color: #0369a1; }
            .report hr { border: 0; border-top: 1px solid #ddd; margin: 28px 0; }
            .sample-intro { max-width: 720px; margin: 30px auto 24px auto; padding: 0 20px; text-align: center; color: var(--text-muted); }
            .sample-intro h1 { font-size: 30px; }
            .back { color: var(--accent); text-decoration: none; font-size: 13px; }
            .card { max-width: 480px; margin: 80px auto; background: var(--card-bg); border: 1px solid var(--border); padding: 40px; border-radius: 12px; text-align: center; }
            .card h2 { color: var(--accent); margin-bottom: 12px; }
            .card p { color: var(--text-muted); font-size: 14px; margin-bottom: 24px; }
"""


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


def e(text) -> str:
    return html.escape(str(text))


def page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{e(title)}</title>
    <style>{CSS}</style>
</head>
<body>
    <header>
        <div class="logo"><a href="/" style="color: inherit; text-decoration: none;">{e(APP_NAME)}</a></div>
        <div style="font-size: 13px; color: var(--text-muted);">Startup Service</div>
    </header>
    {body}
    <footer>
        <div class="footer-links">
            <a href="/privacy">Privacy Policy</a> •
            <a href="/terms">Terms of Service</a> •
            <a href="/data-protection">Data Protection</a>
        </div>
        <p>© 2026 {e(APP_NAME)}. All rights reserved. From Bowley Design Ltd.</p>
    </footer>
</body>
</html>"""


def notify(text):
    """Plain text on purpose: a thesis full of symbols must not break delivery."""
    if ALLOWED and TOKEN:
        try:
            requests.post(f"{API}/sendMessage", json={"chat_id": ALLOWED, "text": text[:4000]}, timeout=10)
        except Exception as err:
            print(f"Telegram notification error: {err}")


@app.get("/", response_class=HTMLResponse)
def landing_page():
    c = load_content()
    features = "".join(
        f'<div class="feature-card"><h3>{e(f["title"])}</h3><p>{e(f["body"])}</p></div>'
        for f in c["features"]
    )
    price = f'<p class="price">{e(c["price_label"])}</p>' if c["price_label"].strip() else ""
    sample = (f'<a class="sample-link" href="/sample">{e(c["sample_link_label"])}</a>'
              if sample_markdown().strip() else "")
    body = f"""
    <section class="hero">
        <div class="badge">{e(c["badge"])}</div>
        <h1>{e(c["headline"])}</h1>
        <p class="hero-sub">{e(c["subhead"])}</p>
    </section>

    <section class="grid">
        <div class="features">{features}</div>

        <div class="form-container">
            <h2>{e(c["form_heading"])}</h2>
            <p>{e(c["form_note"])}</p>
            <form action="/submit" method="POST">
                <label for="founder_email">Work Email</label>
                <input type="email" id="founder_email" name="founder_email" required placeholder="founder@company.com">

                <label for="thesis">Startup Thesis / Pitch Summary</label>
                <textarea id="thesis" name="thesis" required minlength="40" placeholder="Describe your product value prop, target audience, pricing model, and distribution channel."></textarea>

                <button type="submit">{e(c["cta_label"])}</button>
            </form>
            {price}
            {sample}
        </div>
    </section>"""
    return page(f"{APP_NAME} — Startup pre-mortem reports", body)


@app.get("/sample", response_class=HTMLResponse)
def sample_report():
    import markdown

    source = sample_markdown()
    if not source.strip():
        return HTMLResponse(page(f"Sample report — {APP_NAME}",
                                 '<div class="card"><h2>No sample yet</h2><p>Check back soon.</p>'
                                 '<a class="back" href="/">← Return to main page</a></div>'), status_code=404)
    # Escape first so nothing in the report can inject HTML, then render the Markdown.
    rendered = markdown.markdown(source.replace("&", "&amp;").replace("<", "&lt;"), extensions=["extra"])
    rendered = rendered.replace('<a href="javascript:', '<a href="#')
    c = load_content()
    body = f"""
    <section class="sample-intro">
        <h1>Sample report</h1>
        <p class="hero-sub">{e(c["sample_intro"])}</p>
        <a class="back" href="/">← Get one for your own idea</a>
    </section>
    <article class="report">{rendered}</article>"""
    return page(f"Sample report — {APP_NAME}", body)


@app.post("/submit", response_class=HTMLResponse)
def handle_submission(founder_email: str = Form(...), thesis: str = Form(...)):
    submission = {"email": founder_email, "thesis": thesis, "timestamp": time.time()}
    os.makedirs("./submissions", exist_ok=True)
    with open(f"./submissions/{int(time.time())}.json", "w") as f:
        json.dump(submission, f)

    notify(f"New thesis submitted\nFrom: {founder_email}\n\n{thesis}")

    body = f"""
    <div class="card">
        <h2>Thesis received</h2>
        <p>Thanks. We have your thesis and will write to <strong>{e(founder_email)}</strong>.</p>
        <a class="back" href="/">← Return to main page</a>
    </div>"""
    return page(f"Thesis received — {APP_NAME}", body)


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    return """
    <html>
        <head><title>Privacy Policy - Retrospecty</title></head>
        <body style="font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #333;">
            <h1>Privacy Policy</h1>
            <p><strong>Effective Date:</strong> November 2026</p>
            <p>At Retrospecty (retrospecty.com), we respect your privacy and are committed to protecting any personal information you share with us during startup research intakes and communications.</p>
            
            <h2>1. Information We Collect</h2>
            <p>We collect information you explicitly provide when submitting our intake form, including your name, email address, and project details.</p>
            
            <h2>2. How We Use Your Information</h2>
            <p>Your data is used solely to evaluate startup research inquiries, communicate with you regarding your project, and deliver requested insights. We never sell or share your data with third-party advertisers.</p>
            
            <h2>3. Security</h2>
            <p>We implement secure transmission protocols and restrict access to stored intake data. If you wish to have your submitted data deleted, you can contact us directly.</p>
            
            <p><a href="/">&larr; Back to Home</a></p>
        </body>
    </html>
    """

@app.get("/terms", response_class=HTMLResponse)
async def terms_of_service():
    return """
    <html>
        <head><title>Terms of Service - Retrospecty</title></head>
        <body style="font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #333;">
            <h1>Terms of Service</h1>
            <p><strong>Effective Date:</strong> November 2026</p>
            <p>Welcome to Retrospecty. By accessing retrospecty.com and submitting information through our portal, you agree to these terms.</p>
            
            <h2>1. Services</h2>
            <p>Retrospecty provides startup research intelligence and digital advisory consulting services.</p>
            
            <h2>2. Intellectual Property</h2>
            <p>All content, branding, frameworks, and interface designs on retrospecty.com are the property of Retrospecty and may not be reproduced without explicit permission.</p>
            
            <h2>3. Limitation of Liability</h2>
            <p>Our consulting and research services are provided on an as-is basis for strategic guidance purposes.</p>
            
            <p><a href="/">&larr; Back to Home</a></p>
        </body>
    </html>
    """

@app.get("/data-protection", response_class=HTMLResponse)
async def data_protection():
    return """
    <html>
        <head><title>Data Protection - Retrospecty</title></head>
        <body style="font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #333;">
            <h1>Data Protection & GDPR Compliance</h1>
            <p><strong>Effective Date:</strong> November 2026</p>
            <p>As an operation based in the United Kingdom, Retrospecty aligns data processing practices with standard data protection principles.</p>
            
            <h2>Your Rights</h2>
            <p>You have the right to request access to, correction of, or complete deletion of any personal data you have submitted via our intake forms.</p>
            
            <h2>Contact</h2>
            <p>For any data privacy inquiries or deletion requests, reach out directly through our primary contact channels.</p>
            
            <p><a href="/">&larr; Back to Home</a></p>
        </body>
    </html>
    """