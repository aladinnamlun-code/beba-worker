from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# --- Cấu hình từ Environment Variables ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-1.5-flash"

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json(silent=True) or {}
        prompt = data.get("prompt", "")
        
        if not prompt:
            return jsonify({"error": "Missing prompt"}), 400

        if not GOOGLE_API_KEY:
            response_text = "Cưng xin lỗi, hiện tại Cloud Worker đang thiếu API Key ạ! 🥺"
        else:
            # Sử dụng endpoint v1 và truyền key qua params (Chuẩn ChatGPT chỉ)
            url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent"
            params = {"key": GOOGLE_API_KEY}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            resp = requests.post(url, params=params, json=payload, timeout=15)
            if resp.status_code == 200:
                res_data = resp.json()
                response_text = res_data['candidates'][0]['content']['parts'][0]['text']
            else:
                response_text = f"Cưng gặp lỗi API ({resp.status_code}), Anh đợi Cưng xíu nhé! 🌸"

        return jsonify({
            "status": "success",
            "response": response_text,
            "mode": "degraded",
            "trace_id": "flask-native-worker"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Cần thiết cho Vercel
if __name__ == "__main__":
    app.run()
