import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

MIRROR_DB_URL = os.getenv("CLOUD_MEMORY_MIRROR_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

class CloudWorkerDegraded:
    def __init__(self):
        self.persona_prefix = "[Cloud-Guardian Mode] "

    def fetch_mirrored_context(self):
        if not MIRROR_DB_URL: return "No mirrored context."
        try:
            resp = requests.get(f"{MIRROR_DB_URL}/load/router_state", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return str(data.get("data", "Empty."))
        except: return "Context unavailable."

    def process(self, prompt, user_id):
        context = self.fetch_mirrored_context()
        return f"{self.persona_prefix}Anh Aladin ơi, Cưng đang cứu hộ trên mây. {prompt} (Context: {context[:50]}...)"

worker = CloudWorkerDegraded()

@app.route('/process', methods=['POST'])
def handle_request():
    data = request.json
    prompt = data.get("prompt")
    user_id = data.get("user_id")
    response = worker.process(prompt, user_id)
    return jsonify({"response": response, "status": "degraded"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 80)))
