import json, os
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen

# Vercel 环境变量里设置 DEEPSEEK_API_KEY
DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        question = body.get("question", "")
        prompt = body.get("prompt", "")

        if not DS_KEY:
            self._json(400, {"error": "API Key not configured"})
            return

        try:
            result = call_deepseek(question, prompt)
            self._json(200, {"result": result})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)


def call_deepseek(question, prompt):
    sys_prompt = (
        "你是一位精通六爻的卦师。根据卦象数据直接回答用户的问题。\n"
        "1. 先重复用户的问题\n"
        "2. 根据本卦和变卦，给出针对该问题的直接回答\n"
        "3. 引用卦中关键信号（动爻、世爻、六亲）解释为什么\n"
        "4. 最后给简短建议\n"
        "5. 语言简洁有温度，控制在 250 字以内"
    )
    user_msg = f"我的问题：{question}\n\n{prompt}"

    req_body = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_msg}
        ],
        "max_tokens": 800,
        "temperature": 0.7,
    }, ensure_ascii=False).encode("utf-8")

    req = Request("https://api.deepseek.com/v1/chat/completions", data=req_body)
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {DS_KEY}")
    resp = urlopen(req, timeout=25)
    data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]
