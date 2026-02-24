from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)

LANGFLOW_UUID = os.environ.get("LANGFLOW_UUID", "")
LANGFLOW_WEBHOOK = "http://host.docker.internal:7860/api/v1/webhook/" + LANGFLOW_UUID

@app.route("/slack", methods=["POST"])
def slack():
    data = request.json

    # Slack URL verification challenge
    if data and data.get("type") == "url_verification":
        print(f"Challenge verification: {data['challenge']}")
        return jsonify({"challenge": data["challenge"]})

    # Přepošli event do Langflow
    print(f"Incoming Slack event: {data}")
    try:
        event = data.get("event", {})

        # Ignoruj zprávy od botů - zabrání zacyklení
        if event.get("bot_id"):
            print("Ignoring bot message, skipping.")
            return jsonify({"ok": True})
        if event.get("subtype") in ("bot_message", "message_changed"):
            print(f"Ignoring subtype: {event.get('subtype')}, skipping.")
            return jsonify({"ok": True})

        text = event.get("text", "")
        channel = event.get("channel", "")
        user = event.get("user", "")

        # Pošli strukturovaný payload kde text je na vrchní úrovni
        payload = {
            "text": text,
            "channel": channel,
            "user": user,
            "raw": data
        }
        print(f"Sending POST to LANGFLOW_WEBHOOK: {LANGFLOW_WEBHOOK}")
        requests.post(LANGFLOW_WEBHOOK, json=payload, timeout=5)
    except Exception as e:
        print(f"Error forwarding to Langflow: {e}")

    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
