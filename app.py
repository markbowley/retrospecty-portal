import os
import json
import time
from fastapi import FastAPI, Form, Request
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

def notify(text):
    if ALLOWED and TOKEN:
        try:
            requests.post(f"{API}/sendMessage", json={"chat_id": ALLOWED, "text": text, "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            print(f"Telegram notification error: {e}")

@app.get("/", response_class=HTMLResponse)
def landing_page():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{APP_NAME} — Autonomous Startup Risk & Pre-Mortem Audit</title>
        <style>
            :root {{
                --bg: #0b0f19;
                --card-bg: #111827;
                --border: #1f2937;
                --accent: #38bdf8;
                --accent-hover: #0284c7;
                --text-main: #f3f4f6;
                --text-muted: #9ca3af;
            }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text-main); line-height: 1.6; padding: 0; display: flex; flex-direction: column; min-height: 100vh; }}
            header {{ padding: 24px 40px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; max-width: 1100px; width: 100%; margin: 0 auto; }}
            .logo {{ font-weight: 700; font-size: 18px; letter-spacing: -0.5px; color: var(--text-main); }}
            .logo span {{ color: var(--accent); }}
            .hero {{ max-width: 900px; margin: 60px auto 40px auto; padding: 0 20px; text-align: center; }}
            .badge {{ background: rgba(56, 189, 248, 0.1); color: var(--accent); border: 1px solid rgba(56, 189, 248, 0.2); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; padding: 6px 14px; border-radius: 20px; display: inline-block; margin-bottom: 20px; }}
            h1 {{ font-size: 42px; font-weight: 800; letter-spacing: -1px; line-height: 1.15; margin-bottom: 16px; color: #ffffff; }}
            .hero-sub {{ font-size: 18px; color: var(--text-muted); max-width: 680px; margin: 0 auto 40px auto; }}
            
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; max-width: 1000px; margin: 0 auto 60px auto; padding: 0 20px; text-align: left; }}
            @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
            
            .features {{ display: flex; flex-direction: column; gap: 24px; justify-content: center; }}
            .feature-card {{ background: var(--card-bg); border: 1px solid var(--border); padding: 20px; border-radius: 8px; }}
            .feature-card h3 {{ font-size: 16px; margin-bottom: 6px; color: var(--accent); }}
            .feature-card p {{ font-size: 14px; color: var(--text-muted); margin: 0; }}
            
            .form-container {{ background: var(--card-bg); border: 1px solid var(--border); padding: 32px; border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }}
            .form-container h2 {{ font-size: 20px; margin-bottom: 8px; }}
            .form-container p {{ font-size: 13px; color: var(--text-muted); margin-bottom: 24px; }}
            label {{ display: block; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; color: var(--text-muted); }}
            input, textarea {{ width: 100%; padding: 12px 14px; background: #0b0f19; border: 1px solid var(--border); border-radius: 6px; color: var(--text-main); font-size: 14px; margin-bottom: 20px; font-family: inherit; }}
            input:focus, textarea:focus {{ outline: none; border-color: var(--accent); }}
            textarea {{ height: 110px; resize: vertical; }}
            button {{ background: var(--accent); color: #0b0f19; border: none; padding: 14px 24px; font-size: 14px; font-weight: 700; border-radius: 6px; cursor: pointer; width: 100%; transition: all 0.2s; }}
            button:hover {{ background: var(--accent-hover); color: white; }}
            
            footer {{ margin-top: auto; border-top: 1px solid var(--border); padding: 30px 40px; font-size: 12px; color: var(--text-muted); text-align: center; }}
            .footer-links {{ margin-bottom: 12px; }}
            .footer-links a {{ color: var(--text-muted); text-decoration: none; margin: 0 10px; }}
            .footer-links a:hover {{ color: var(--text-main); }}
        </style>
    </head>
    <body>
        <header>
            <div class="logo"><span></span>{APP_NAME}</div>
            <div style="font-size: 13px; color: var(--text-muted);">Startup Service</div>
        </header>

        <section class="hero">
            <div class="badge">Engineered for Founders & Investors</div>
            <h1>Stress-test your startup thesis before spending a single dollar.</h1>
            <p class="hero-sub">Submit your product concept or expansion strategy. {APP_NAME} autonomously cross-references historical failure modes, unit economics traps, and go-to-market blindspots.</p>
        </section>

        <section class="grid">
            <div class="features">
                <div class="feature-card">
                    <h3>1. Historical autopsy cross-matching</h3>
                    <p>Cross-examines your business model against vectorized failure case studies from past startups in your sector.</p>
                </div>
                <div class="feature-card">
                    <h3>2. Margin & CAC trap detection</h3>
                    <p>Identifies structural unit-economic flaws, customer acquisition traps, and hidden infrastructure scaling overheads.</p>
                </div>
                <div class="feature-card">
                    <h3>3. Executive briefing output</h3>
                    <p>Receive a clear, objective breakdown highlighting top risk vectors and mitigation strategies directly to your inbox.</p>
                </div>
            </div>

            <div class="form-container">
                <h2>Request audit</h2>
                <p>Confidential and automated. We processes entries continuously.</p>
                <form action="/submit" method="POST">
                    <label for="founder_email">Work Email</label>
                    <input type="email" id="founder_email" name="founder_email" required placeholder="founder@company.com">
                    
                    <label for="thesis">Startup Thesis / Pitch Summary</label>
                    <textarea id="thesis" name="thesis" required placeholder="Describe your product value prop, target audience, pricing model, and distribution channel."></textarea>
                    
                    <button type="submit">Run audit →</button>
                </form>
            </div>
        </section>

        <footer>
            <div class="footer-links">
                <a href="/privacy">Privacy Policy</a> • 
                <a href="/terms">Terms of Service</a> • 
                <a href="/data-protection">Data Protection</a>
            </div>
            <p>© 2026 {APP_NAME}. All rights reserved. From Bowley Design Ltd.</p>
        </footer>
    </body>
    </html>
    """

@app.post("/submit", response_class=HTMLResponse)
def handle_submission(founder_email: str = Form(...), thesis: str = Form(...)):
    submission = {"email": founder_email, "thesis": thesis, "timestamp": time.time()}
    os.makedirs("./submissions", exist_ok=True)
    with open(f"./submissions/{int(time.time())}.json", "w") as f:
        json.dump(submission, f)
    
    notify(f"📥 *New Startup Intake Received!*\n• *From:* `{founder_email}`\n• *Thesis:* {thesis}\n\n*(Reply `/analyze {thesis}` to run detailed manual check)*")
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Audit Queued — {APP_NAME}</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; background: #0b0f19; color: #f3f4f6; padding: 60px 20px; text-align: center; }}
        .card {{ max-width: 480px; margin: 0 auto; background: #111827; border: 1px solid #1f2937; padding: 40px; border-radius: 12px; }}
        h2 {{ color: #38bdf8; margin-bottom: 12px; }}
        p {{ color: #9ca3af; font-size: 14px; margin-bottom: 24px; line-height: 1.5; }}
        a {{ color: #38bdf8; text-decoration: none; font-size: 13px; }}
    </style>
    </head>
    <body>
        <div class="card">
            <h2>Thesis Received</h2>
            <p>{APP_NAME} has ingested your thesis for <strong>{founder_email}</strong>. Our autonomous risk engine is generating your structural audit now.</p>
            <a href="/">← Return to main page</a>
        </div>
    </body>
    </html>
    """