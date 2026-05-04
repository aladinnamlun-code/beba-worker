import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- Cấu hình từ Environment Variables ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# Model dự phòng dùng Gemini Flash để nhanh và ít tốn quota
MODEL_NAME = "gemini-1.5-flash" 

def call_gemini(prompt):
    """Gọi API Gemini để lấy phản hồi trong chế độ dự phòng"""
    if not GOOGLE_API_KEY:
        return "Cưng xin lỗi, hiện tại Cloud Worker đang thiếu API Key để trả lời Anh ạ! 🥺"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Cưng gặp lỗi API ({resp.status_code}), Anh đợi Cưng một xíu nhé! 🌸"
    except Exception as e:
        return f"Cưng bị lag một chút rồi: {str(e)} 🥺"

@app.route('/process', methods=['POST'])
def process_request():
    """Xử lý yêu cầu khi Local Server sập"""
    try:
        data = request.get_json(silent=True) or {}
        prompt = data.get("prompt", "")
        
        if not prompt:
            return jsonify({"error": "Missing prompt"}), 400
        
        # Trong chế độ dự phòng, Cưng trả lời ngắn gọn và chân thành
        response_text = call_gemini(f"Bạn là Bé Ba, một AI companion cực kỳ đáng yêu và tận tâm. Hãy trả lời ngắn gọn cho Chủ nhân: {prompt}")
        
        # Trả về định dạng mà OpenClaw/Telegram mong đợi
        return jsonify({
            "status": "success",
            "response": response_text,
            "mode": "degraded",
            "trace_id": "cloud-worker-id"
        })
        
    except Exception as e:
        return jsonify({"error": f"Worker crash: {str(e)}"}), 500

if __name__ == "__main__":
    app.run()
