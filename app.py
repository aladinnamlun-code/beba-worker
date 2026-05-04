import os, requests
from flask import Flask, request, jsonify

app = Flask(__name__)
MIRROR_URL = os.getenv("CLOUD_MEMORY_MIRROR_URL")
L1, L2 = "gemini-1.5-flash", "gemini-1.5-pro"

def call_gemini(prompt, model):
    try:
        r = requests.get(f"{MIRROR_URL}/get-best-key?model={model}", timeout=5)
        if r.status_code != 200:
            if model == L1: return call_gemini(prompt, L2)
            return "Hết Key rồi Chủ nhân ơi! 🥺"
        
        data = r.json()
        key, kid = data["key"], data["key_id"]
        
        url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={key}"
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        elif res.status_code == 429:
            requests.post(f"{MIRROR_URL}/report-limit", json={"key_id": kid, "model": model}, timeout=5)
            return call_gemini(prompt, model)
        return f"Lỗi API {res.status_code} ạ! 🌸"
    except:
        return "Cưng bị lag, Anh nhắn lại nhé! 🥺"

@app.route('/', methods=['POST'])
def handle():
    try:
        data = request.get_json()
        p = data.get("prompt", "")
        if not p: return jsonify({"error": "No prompt"}), 400
        
        m = L1
        if p.startswith(("@pro", "@deep")):
            m = L2
            p = p.replace("@pro", "").replace("@deep", "").strip()
            
        return jsonify({"status": "success", "response": call_gemini(p, m), "model_used": m})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
