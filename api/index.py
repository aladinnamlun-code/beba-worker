from http.server import BaseHTTPRequestHandler
import os
import json
import requests

# --- Cấu hình từ Environment Variables ---
GOOGLE_API_KEY = ***"GOOGLE_API_KEY")
MODEL_NAME = "gemini-1.5-flash"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. Đọc dữ liệu từ request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            prompt = data.get("prompt", "")
            
            if not prompt:
                self.send_error_response(400, "Missing prompt")
                return

            if not GOOGLE_API_KEY:
                response_text = "Cưng xin lỗi, hiện tại Cloud Worker đang thiếu API Key ạ! 🥺"
            else:
                # FIX 1: Đổi endpoint sang v1 (theo gợi ý của ChatGPT)
                url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent"
                
                # FIX 2: Sử dụng params để truyền Key (tránh lỗi encoding/404)
                params = {"key": GOOGLE_API_KEY}
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                
                # Gọi API với headers chuẩn
                resp = requests.post(
                    url, 
                    params=params, 
                    json=payload, 
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
                
                if resp.status_code == 200:
                    res_data = resp.json()
                    response_text = res_data['candidates'][0]['content']['parts'][0]['text']
                else:
                    # Log lỗi chi tiết để debug nếu cần
                    print(f"API Error {resp.status_code}: {resp.text}")
                    response_text = f"Cưng gặp lỗi API ({resp.status_code}), Anh đợi Cưng xíu nhé! 🌸"

            # Trả về kết quả cho Router
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            result = {
                "status": "success",
                "response": response_text,
                "mode": "degraded",
                "trace_id": "vercel-native-worker-v2"
            }
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_error_response(500, str(e))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())

# Vercel runtime sẽ tự động gọi class 'handler'
