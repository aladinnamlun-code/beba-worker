from http.server import BaseHTTPRequestHandler
import os
import json
import requests

MIRROR_URL = os.getenv("CLOUD_MEMORY_MIRROR_URL")
MODEL_L1 = "gemini-1.5-flash"
MODEL_L2 = "gemini-1.5-pro"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            prompt = data.get("prompt", "")
            if not prompt:
                                self.send_error_response(400, "Missing prompt")
                return

            # 1. Kiểm tra lệnh ép model (@pro hoặc @deep)
            target_model = MODEL_L1
            if prompt.startswith("@pro") or prompt.startswith("@deep"):
                target_model = MODEL_L2
                prompt = prompt.replace("@pro", "").replace("@deep", "").strip()

            # 2. Thực hiện gọi API với cơ chế luân chuyển
            response_text = self.call_gemini_with_rotation(prompt, target_model)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "response": response_text,
                "model_used": target_model,
                "mode": "hybrid-rotation"
            }).encode())

        except Exception as e:
            self.send_error_response(500, str(e))

    def call_gemini_with_rotation(self, prompt, model):
        """Logic đệ quy: Lấy Key -> Gọi API -> Nếu lỗi 429 thì báo Mirror và thử Key khác"""
        try:
            # A. Lấy key nhàn rỗi nhất từ Mirror
            key_resp = requests.get(f"{MIRROR_URL}/get-best-key?model={model}", timeout=5)
            if key_resp.status_code != 200:
                # Nếu L1 hết key -> Tự nâng cấp lên L2
                if model == MODEL_L1:
                    return self.call_gemini_with_rotation(prompt, MODEL_L2)
                return "Cưng xin lỗi, toàn bộ Key đều đã hết quota rồi ạ! 🥺"
            
            key_data = key_resp.json()
            api_key = key_data["key"]
            key_id = key_data["key_id"]
        except Exception:
            return "Cưng không thể kết nối với Mirror để lấy Key ạ! 🌸"

        # B. Gọi Gemini API
        url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                return resp.json()['candidates'][0]['content']['parts'][0]['text']
            
            elif resp.status_code == 429:
                # Báo cho Mirror đưa key này vào Cooldown
                requests.post(f"{MIRROR_URL}/report-limit", 
                              json={"key_id": key_id, "model": model}, timeout=5)
                # Đệ quy: Thử lại để lấy Key khác
                return self.call_gemini_with_rotation(prompt, model)
            else:
                return f"Cưng gặp lỗi API ({resp.status_code}) khi dùng model {model} ạ! 🌸"
        except Exception:
            return "Cưng bị lag một chút khi gọi Gemini, Anh nhắn lại nhé! 🥺"

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())
