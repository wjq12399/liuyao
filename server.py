"""
六爻玄鉴 · 一体化服务器（网页 + AI 解卦）
启动后电脑和手机都能访问
"""
import json, os, sys, io, socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.request import Request, urlopen

PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))

# --- 获取本机局域网 IP ---
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

# --- 读 API Key ---
DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

import argparse as _ap
_ap_parser = _ap.ArgumentParser()
_ap_parser.add_argument("--deepseek-key", default="")
_args, _ = _ap_parser.parse_known_args()
if _args.deepseek_key: DS_KEY = _args.deepseek_key

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/interpret":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            question = body.get("question", "")
            prompt = body.get("prompt", "")

            if not DS_KEY:
                self._json(400, {"error": "服务器未配置 API Key"})
                return

            try:
                result = self._call_ds(question, prompt)
                self._json(200, {"result": result})
            except Exception as e:
                self._json(500, {"error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()

    def _call_ds(self, question, prompt):
        sys_prompt = (
            "你是一位精通六爻的卦师。你根据卦象数据直接回答用户的问题。\n"
            "规则：\n"
            "1. 先重复用户的问题\n"
            "2. 根据本卦和变卦，给出针对该问题的直接回答\n"
            "3. 引用卦中关键信号（动爻、世爻、六亲）解释为什么\n"
            "4. 最后给简短建议\n"
            "5. 语言简洁有温度，像朋友聊天，控制在 250 字以内"
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
        resp = urlopen(req, timeout=30)
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def _json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    ip = get_ip()

    print(f"\n  >>>  六爻玄鉴 服务器已启动  <<<")
    print(f"  电脑访问: http://localhost:{PORT}")
    print(f"  手机访问: http://{ip}:{PORT}")
    print(f"  AI 解卦: {'[OK]' if DS_KEY else '[WARN] 未配置 API Key'}")
    print(f"\n  按 Ctrl+C 停止\n")

    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
