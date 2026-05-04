import os, requests
from flask import Flask, request, jsonify

app = Flask(__name__)
MIRROR_URL = os.getenv("CLOUD_MEMORY_MIRROR_URL")

# Định nghĩa các Model theo tầng
L1_MODEL = "gemini-1.5-flash"
L2_MODELS = ["gemini-1.5-pro", "gpt-5.4"]
L3_MODEL = "llama-3.1-70b" 

def call_api(provider, model, key, prompt):
    """Hàm gọi API cho từng nhà cung cấp"""
    try:
        if provider == "google":
            url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key=***"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                return resp.json()['candidates'][0]['content']['parts'][0]['text'], resp.status_code
        
        elif provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}"}
            payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'], resp.status_code
        
        elif provider == "groq": 
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}"}
            payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'], resp.status_code
                
        return None, 500
    except:
        return None, 500

def rotate_and_call(prompt, model_target):
    """Logic luân chuyển đa tầng: L1 -> L2 -> L3"""
    model = model_target if model_target else L1_MODEL
    search_list = [model]
    if model == L1_MODEL:
        search_list.extend(L2_MODELS + [L3_MODEL])
    elif model in L2_MODELS:
        search_list.extend([m for m in L2_MODELS if m != model] + [L3_MODEL])
    else:
        search_list.append(L3_MODEL)

    for target in search_list:
        try:
            r = requests.get(f"{MIRROR_URL}/get-best-key?model={target}", timeout=5)
            if r.status_code != 200: continue
            
            data = r.json()
            key, kid = data["key"], data["key_id"]
            
            if "gemini" in target: provider = "google"
            elif "gpt" in target: provider = "openai"
            elif "llama" in target: provider = "groq"
            else: provider = "unknown"
            
            res_text, status = call_api(provider, target, key, prompt)
            
            if res_text:
                return res_text, target
            
            if status == 429:
                requests.post(f"{MIRROR_URL}/report-limit", json={"key_id": kid, "model": target}, timeout=5)
                continue
        except:
            continue
            
    return "Cưng xin lỗi, tất cả các tầng Model đều đang quá tải rồi ạ! 🥺", "None"

@app.route('/', methods=['POST'])
def handle():
    try:
        data = request.get_json()
        p = data.get("prompt", "")
                if not p: return jsonify({"error": "No prompt"}), 400
        
        m = None
        if p.startswith(("@pro", "@deep")):
            m = "gpt-5.4" 
            p = p.replace("@pro", "").replace("@deep", "").strip()
        elif p.startswith("@llama"): # Thêm lệnh gọi đích danh Llama
            m = "llama-3.1-70b"
            p = p.replace("@llama", "").strip()
            
        response, model_used = rotate_and_call(p, m)
        return jsonify({"status": "success", "response": response, "model_used": model_used})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
