import os
import json
import logging
import boto3
from playwright.sync_api import sync_playwright
import hashlib
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# === Artist Variations List ===
ARTISTS = {
    "Tuna": ["tuna", "טונה", "Tuna"],
    "Ravid Plotnik": ["Ravid Plotnik", "Ravid Plotnik", "נצ׳י נצ׳", "רביד פלוטניק", "ravid plotnik"],
    "Shazamat": ["Shazamat", "שזהמט", "shazamat","שאזאמאט"],
}

def scrape_shows():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process',
                    '--no-zygote'
                ]
            )
            context = browser.new_context()
            page = context.new_page()
            
            try:
                page.goto("https://barby.co.il", timeout=60000)
                page.wait_for_timeout(4000)

                data = page.evaluate("""() => {
                    return fetch("https://barby.co.il/api/shows/find", {
                        method: "GET",
                        headers: { "Accept": "application/json" },
                        credentials: "same-origin"
                    }).then(res => res.json());
                }""")

                return data.get("returnShow", {}).get("show", [])
            finally:
                context.close()
                browser.close()
    except Exception as e:
        logger.error(f"Failed to scrape shows: {str(e)}")
        print(f'failed to scrape shows: {str(e)}')
        return []

def find_matching_shows(shows, artist_variants):
    results = []
    for artist, variations in artist_variants.items():
        for show in shows:
            name = show.get("showName", "")
            if any(variant in name for variant in variations):
                results.append((artist, show))
    return results

def format_report(matched_shows):
    body = "🎶 הופעות חדשות שזוהו:\n\n"
    for artist, show in matched_shows:
        body += f"🎤 {artist}: {show['showName']}\n📅 {show['showDate']} {show['showTime']}\n💰 {show['showPrice']}₪\n🔗 https://barby.co.il/event/{show['showId']}\n\n"
    return body

def send_sns_notification(subject, message, topic_arn):
    sns_client = boto3.client('sns')
    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject
        )
        logger.info(f"✅ SNS notification sent! Message ID: {response['MessageId']}")
        print(f'SNS notification sent! Message ID: {response["MessageId"]}')
        return True
    except Exception as e:
        logger.error(f"Failed to send SNS notification: {str(e)}")
        print(f'Failed to send SNS notification: {str(e)}')
        return False

def handler(event, context):
    try:
        logger.info("📡 Starting show scraping process...")
        print("📡 Starting show scraping process...")
        all_shows = scrape_shows()

        logger.info("🎯 Matching artists...")
        print("🎯 Matching artists...")
        matched = find_matching_shows(all_shows, ARTISTS)

        print(f'matched: {matched}')

        if matched:
            email_body = format_report(matched)
            # Send notification using SNS
            send_sns_notification(
                subject="🎵 דיווח הופעות מעודכנות",
                message=email_body,
                topic_arn="arn:aws:sns:eu-west-1:730335436836:BarbieScanner"
            )
            return {"status": "success", "matches_found": len(matched)}
        else:
            logger.info("ℹ️ No shows matched the tracked artists.")
            print("ℹ️ No shows matched the tracked artists.")
            return {"status": "success", "matches_found": 0}
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        print(f'Error in handler: {str(e)}')
        return {"status": "error", "error": str(e)}
