from http.server import BaseHTTPRequestHandler
import os
import json
import requests

# --- Cấu hình từ Environment Variables ---
# Lấy Key trực tiếp từ Env của Vercel, không ghi cứng vào code
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-1.5-flash"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            prompt = data.get("prompt", "")
            
            if not prompt:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing prompt"}).encode())
                return

            if not GOOGLE_API_KEY:
                response_text = "Cưng xin lỗi, hiện tại Cloud Worker đang thiếu API Key ạ! 🥺"
            else:
                # URL gọi Gemini API sử dụng biến GOOGLE_API_KEY
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                
                resp = requests.post(url, json=payload, timeout=15)
                if resp.status_code == 200:
                    res_data = resp.json()
                    response_text = res_data['candidates'][0]['content']['parts'][0]['text']
                else:
                    response_text = f"Cưng gặp lỗi API ({resp.status_code}), Anh đợi Cưng xíu nhé! 🌸"

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            result = {
                "status": "success",
                "response": response_text,
                "mode": "degraded",
                "trace_id": "vercel-native-worker"
            }
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
