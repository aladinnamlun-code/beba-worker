import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Cấu hình từ Environment Variables ---
MIRROR_URL = os.getenv("CLOUD_MEMORY_MIRROR_URL")
MODEL_L1 = "gemini-1.5-flash"
MODEL_L2 = "gemini-1.5-pro"

def call_gemini_with_rotation(prompt, model):
    """Logic luân chuyển Key và Model đệ quy"""
    try:
        # A. Lấy key nhàn rỗi nhất từ Mirror
        key_resp = requests.get(f"{MIRROR_URL}/get-best-key?model={model}", timeout=5)
        if key_resp.status_code != 200:
            # Nếu model hiện tại không còn key -> Thử nâng cấp model (L1 -> L2)
            if model == MODEL_L1:
                return call_gemini_with_rotation(prompt, MODEL_L2)
            return "Cưng xin lỗi, toàn bộ Key của mọi model đều đã hết quota rồi ạ! 🥺"
        
        key_data = key_resp.json()
        api_key = key_data["key"]
        key_id = key_data["key_id"]
    except Exception:
        return "Cưng không thể kết nối với Mirror để lấy Key ạ! 🌸"

    # B. Gọi Gemini API - ĐÃ SỬA CHUẨN {api_key}
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        
        elif resp.status_code == 429:
            # Báo cáo limit lên Mirror để đưa key vào Cooldown
            requests.post(f"{MIRROR_URL}/report-limit", 
                          json={"key_id": key_id, "model": model}, timeout=5)
            # Đệ quy: Thử lại với key khác
            return call_gemini_with_rotation(prompt, model)
        else:
            return f"Cưng gặp lỗi API ({resp.status_code}) khi dùng model {model} ạ! 🌸"
    except Exception:
        return "Cưng bị lag một chút khi gọi Gemini, Anh nhắn lại nhé! 🥺"

@app.route('/', methods=['POST'])
def handle_request():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        prompt = data.get("prompt", "")
        if not prompt:
            return jsonify({"error": "Missing prompt"}), 400

        # 1. KIỂM TRA LỆNH ĐIỀU PHỐI (Manual Override)
        target_model = MODEL_L1
        if prompt.startswith("@pro") or prompt.startswith("@deep"):
            target_model = MODEL_L2
            prompt = prompt.replace("@pro", "").replace("@deep", "").strip()

        # 2. THỰC HIỆN LUÂN CHUYỂN (Hybrid Rotation)
        response_text = call_gemini_with_rotation(prompt, target_model)
              return jsonify({
            "status": "success",
            "response": response_text,
            "model_used": target_model,
            "mode": "hybrid-rotation"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
  app.run()
