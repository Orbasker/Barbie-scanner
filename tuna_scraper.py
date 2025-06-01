import os
import json
import base64
from email.message import EmailMessage
from playwright.async_api import async_playwright
import asyncio
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Load environment ===
load_dotenv()
GMAIL_KEY = os.getenv("GMAIL_KEY")  # not used directly in Gmail API

# === Gmail API Setup ===
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def gmail_authenticate():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("creds.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def send_gmail_report(service, to, subject, body):
    message = EmailMessage()
    message.set_content(body)
    message["To"] = to
    message["From"] = "me"
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send_message = { "raw": encoded_message }

    try:
        send = service.users().messages().send(userId="me", body=send_message).execute()
        logger.info(f"✅ Message sent! ID: {send['id']}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

# === Artist Variations List ===
ARTISTS = {
    "Tuna": ["tuna", "טונה", "Tuna"],
    "Ravid Plotnik": ["Ravid Plotnik", "Ravid Plotnik", "נצ׳י נצ׳", "רביד פלוטניק", "ravid plotnik"],
}

# === Scraper via Playwright (JS context) ===
async def scrape_shows():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://barby.co.il", timeout=60000)
            await page.wait_for_timeout(4000)

            data = await page.evaluate("""() => {
                return fetch("https://barby.co.il/api/shows/find", {
                    method: "GET",
                    headers: { "Accept": "application/json" },
                    credentials: "same-origin"
                }).then(res => res.json());
            }""")

            await browser.close()
            return data.get("returnShow", {}).get("show", [])
    except Exception as e:
        logger.error(f"Failed to scrape shows: {str(e)}")
        return []

# === Match Artists ===
def find_matching_shows(shows, artist_variants):
    results = []
    for artist, variations in artist_variants.items():
        for show in shows:
            name = show.get("showName", "")
            if any(variant in name for variant in variations):
                results.append((artist, show))
    return results

# === Format Message ===
def format_report(matched_shows):
    body = "🎶 הופעות חדשות שזוהו:\n\n"
    for artist, show in matched_shows:
        body += f"🎤 {artist}: {show['showName']}\n📅 {show['showDate']} {show['showTime']}\n💰 {show['showPrice']}₪\n🔗 https://barby.co.il/event/{show['showId']}\n\n"
    return body

# === Main function to be called by scheduler ===
async def scrape_and_notify():
    try:
        logger.info("📡 Starting show scraping process...")
        all_shows = await scrape_shows()

        logger.info("🎯 Matching artists...")
        matched = find_matching_shows(all_shows, ARTISTS)

        if matched:
            email_body = format_report(matched)
            service = gmail_authenticate()
            success = send_gmail_report(
                service,
                to="orbasker@gmail.com",  # <- Change this
                subject="🎵 דיווח הופעות מעודכנות",
                body=email_body
            )
            return {"status": "success" if success else "error", "matches_found": len(matched)}
        else:
            logger.info("ℹ️ No shows matched the tracked artists.")
            return {"status": "success", "matches_found": 0}
    except Exception as e:
        logger.error(f"Error in scrape_and_notify: {str(e)}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    asyncio.run(scrape_and_notify())
    # running
