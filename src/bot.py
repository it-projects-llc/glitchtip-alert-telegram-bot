import logging
import os

import requests
from dotenv import load_dotenv
from flask import Flask, request

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALERT_CHAT_ID = os.getenv("ALERT_CHAT_ID")
DEBUG_MODE = int(os.getenv("DEBUG_MODE", "0"))

# Configure logging
if DEBUG_MODE:
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logging.debug("Debug mode enabled")
else:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

app = Flask(__name__)


def escape_markdown_v2(text):
    """Escapes characters for Telegram MarkdownV2."""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in str(text))


@app.route("/", methods=["POST", "GET"])
def glitchtip_webhook():
    if request.method == "GET":
        logging.debug("Received GET request at root '/'")
        return "OK", 200

    logging.debug("Received POST request at root '/'")
    payload = request.json

    if payload and payload.get("alias") == "GlitchTip":
        try:
            attachments = payload.get("attachments", [])
            messages = []

            # Iterate through all attachments and build a list of formatted messages
            for att in attachments:
                title = att.get("title", "No title")
                link = att.get("title_link", "")
                fields = att.get("fields", [])

                project = ""
                environment = ""
                release = ""

                for field in fields:
                    field_title = field.get("title")
                    field_value = field.get("value")

                    if field_title == "Project":
                        project = field_value
                    elif field_title == "Environment":
                        environment = field_value
                    elif field_title == "Release":
                        release = field_value

                # Escape values for MarkdownV2
                title = escape_markdown_v2(title)
                project = escape_markdown_v2(project)
                environment = escape_markdown_v2(environment)
                release = escape_markdown_v2(release)
                link = escape_markdown_v2(link)

                # Format the message for a single issue using MarkdownV2
                issue_message = (
                    f"*Title*: {title}\n"
                    f"*Project*: {project}\n"
                    f"*Environment*: {environment}\n"
                    f"*Release*: {release}\n"
                    f"*Link*: {link}"
                )
                messages.append(issue_message)

            if messages:
                # Combine all formatted issues into a single message
                separator = "\n\n*New GlitchTip Event*\n\n"
                combined_message = "*New GlitchTip Event*\n\n" + separator.join(
                    messages
                )
                send_telegram_message(
                    ALERT_CHAT_ID, combined_message, parse_mode="MarkdownV2"
                )
        except Exception as e:
            logging.exception(f"Error processing GlitchTip payload: {e}")
    else:
        logging.warning("Received POST with empty or invalid payload")

    return "OK", 200


def send_telegram_message(chat_id, text, parse_mode=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode

    logging.debug(f"Sending message to Telegram: {data}")
    try:
        r = requests.post(url, json=data, timeout=60)
        logging.debug(f"Telegram response: {r.status_code} {r.text}")
    except Exception as e:
        logging.exception(f"Error sending message to Telegram: {e}")


if __name__ == "__main__":
    port = 8844
    logging.info(f"Starting server on port {port} (debug={DEBUG_MODE})")
    app.run(host="0.0.0.0", port=port)
