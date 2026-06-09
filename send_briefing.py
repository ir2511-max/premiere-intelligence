#!/usr/bin/env python3
"""
Premiere Intelligence - Daily Email Briefing
Runs every weekday at 7:30 AM ET via GitHub Actions.
"""

import os, json, anthropic, httpx, re
from datetime import datetime
from zoneinfo import ZoneInfo

# -- CONFIG --
RECIPIENTS   = ["ir2511@columbia.edu"]
SENDER_EMAIL = "onboarding@resend.dev"
SENDER_NAME  = "Premiere Intelligence"

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
RESEND_API_KEY    = os.environ["RESEND_API_KEY"]

# -- PROMPT --
SYSTEM_PROMPT = """You are the editor of "Premiere Intelligence," a daily luxury-tech intelligence briefing for senior executives at LVMH. Your reader works in Media Data & Performance at a world-class luxury conglomerate.

Your job: surface 5-8 of the most signal-rich stories from TODAY at the intersection of:
- AI + luxury fashion (LVMH, Kering, Richemont, Hermes, Prada, etc.)
- AI + media / advertising / performance marketing
- Media, data & tech shaping the luxury industry

CRITICAL RULES:
1. Only include stories you are highly confident are REAL, recent (last 48h), and verifiable. If uncertain, omit.
2. Every story MUST have a real, working URL from a credible publication.
3. Write in a sharp, confident editorial voice - no fluff, no hedging.
4. Score each story 1-5 for relevance to a luxury media executive.
5. Assign each story one category from: MAISONS & BRANDS, CREATIVE & CAMPAIGNS, POLICY & RISK, COMMERCE & RETAIL, DATA & PERFORMANCE, MEDIA & PLATFORMS.

Return ONLY valid JSON, no markdown, no preamble:
{
  "date": "Day, D Month YYYY",
  "lede": "One sentence editorial summary of today's signal.",
  "stories": [
    {
      "category": "MAISONS & BRANDS",
      "score": 5,
      "headline": "Story headline here",
      "summary": "3-4 sentence sharp editorial summary.",
      "source": "Publication Name",
      "url": "https://real-article-url.com"
    }
  ]
}"""

# -- FETCH BRIEFING --
def fetch_briefing(today_str):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Today is {today_str}. Search for the most important real news stories from the last 24-48 hours at the intersection of AI, luxury, media, and technology. Return only verified, linkable stories in the JSON format specified."
        }]
    )

    text = "".join(b.text for b in response.content if b.type == "text")
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_match:
        clean = json_match.group(1).strip()
    else:
        start = text.find("{")
        end = text.rfind("}")
        clean = text[start:end+1] if start != -1 and end != -1 else text.strip()
    return json.loads(clean)

# -- BUILD EMAIL --
def build_email(data):
    stories_html = ""
    for s in sorted(data["stories"], key=lambda x: -x["score"]):
        pips = "".join(
            f'<span style="display:inline-block;width:10px;height:4px;border-radius:1px;background:{"#9a8a6a" if i < s["score"] else "#ddd"};margin-right:2px;"></span>'
            for i in range(5)
        )
        read_link = f'<a href="{s["url"]}" style="font-size:10px;letter-spacing:0.1em;color:#9a8a6a;text-decoration:none;text-transform:uppercase;">Read</a>' if s.get("url","").startswith("http") else ""

        stories_html += f"""
        <tr><td style="padding:28px 0;border-bottom:1px solid #d8d0c4;">
          <div style="margin-bottom:8px;">
            <span style="font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:#6b6560;">{s["category"]}</span>
          </div>
          <h2 style="font-family:Georgia,serif;font-size:22px;font-weight:600;line-height:1.2;margin:0 0 10px;color:#1a1a18;">{s["headline"]}</h2>
          <p style="font-size:13px;line-height:1.7;color:#3a3830;margin:0 0 12px;">{s["summary"]}</p>
          <span style="font-size:10px;letter-spacing:0.08em;color:#6b6560;margin-right:16px;">{s["source"]}</span>
          {read_link}
        </td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0ebe0;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0ebe0;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
        <tr><td style="padding-bottom:6px;">
          <p style="font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:#6b6560;margin:0;">{data["date"]}</p>
        </td></tr>
        <tr><td style="border-bottom:2px solid #1a1a18;padding-bottom:16px;">
          <h1 style="font-family:Georgia,serif;font-size:48px;font-weight:600;line-height:0.92;margin:0;color:#1a1a18;">PREMIERE<br>INTELLIGENCE</h1>
          <p style="font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:#6b6560;margin:10px 0 0;">The luxury-tech briefing</p>
        </td></tr>
        <tr><td style="border-bottom:1px solid #c8c2b4;padding:20px 0;">
          <p style="font-family:Georgia,serif;font-style:italic;font-size:16px;line-height:1.6;color:#1a1a18;margin:0;">{data["lede"]}</p>
        </td></tr>
        {stories_html}
        <tr><td style="padding-top:32px;text-align:center;">
          <p style="font-size:9px;letter-spacing:0.14em;text-transform:uppercase;color:#c8c2b4;margin:0;">
            Premiere Intelligence &nbsp;·&nbsp; The luxury-tech briefing &nbsp;·&nbsp; Delivered weekdays at 7:30 AM
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

# -- SEND EMAIL --
def send_email(subject, html):
    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json={
            "from": f"{SENDER_NAME} <{SENDER_EMAIL}>",
            "to": RECIPIENTS,
            "subject": subject,
            "html": html,
        },
        timeout=30,
    )
    response.raise_for_status()
    print(f"Email sent to {RECIPIENTS}")
    return response.json()

# -- MAIN --
def main():
    et = ZoneInfo("America/New_York")
    today_str = datetime.now(et).strftime("%A, %d %B %Y")
    print(f"Fetching briefing for {today_str}...")

    data = fetch_briefing(today_str)

    if not data.get("stories"):
        print("No stories found today - skipping email.")
        return

    print(f"Found {len(data['stories'])} stories.")
    html = build_email(data)
    subject = f"Premiere Intelligence - {today_str}"
    send_email(subject, html)

if __name__ == "__main__":
    main()
