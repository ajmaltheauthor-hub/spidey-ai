r"""
Spidey AI — Ultra-Light Cloud AI & Video Relay Server
Runs directly from Google Drive (G:\My Drive\Spidey-AI) with ~15 MB RAM.
Zero local AI engine (No Ollama / No local GPU weights required).
"""

import base64
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import hydrogen_video_engine
except ImportError:
    hydrogen_video_engine = None

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
ENV_FILE = BASE_DIR / ".env"
VIDEOS_DIR = BASE_DIR / "videos"
AUDIO_DIR = BASE_DIR / "audio"
TEMP_DIR = BASE_DIR / "temp_render"

for d in (VIDEOS_DIR, AUDIO_DIR, TEMP_DIR):
    d.mkdir(parents=True, exist_ok=True)


def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


ENV = load_env()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or ENV.get("GEMINI_API_KEY", "")
KIE_API_KEY = os.getenv("KIE_API_KEY") or ENV.get("KIE_API_KEY") or ENV.get("ALL_MODELS_API_KEY", "")

# Locate FFmpeg (WinGet / Program Files / PATH)
FFMPEG_PATHS = [
    shutil.which("ffmpeg"),
    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    r"C:\Users\T470s\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe",
]
FFMPEG_BIN = next((p for p in FFMPEG_PATHS if p and Path(p).exists()), None)


def mask_key(k: str) -> str:
    if not k:
        return "Not Set"
    return f"{k[:4]}...{k[-4:]}" if len(k) > 8 else "****"


def http_json(url: str, method: str = "GET", payload: dict | None = None, headers: dict | None = None, timeout: int = 30) -> tuple[int, dict]:
    req_headers = {"User-Agent": "SpideyAI/1.0"}
    if headers:
        req_headers.update(headers)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw}


class SpideyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, format, *args):
        # Quiet logging to avoid console spam
        pass

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Block direct download of .env or server.py
        if path.lower() in ("/.env", "/server.py"):
            self.send_json({"error": "Access denied"}, status=403)
            return

        if path == "/api/ollama/status":
            ollama_exe = r"C:\Users\T470s\AppData\Local\Programs\Ollama\ollama.exe"
            installed = os.path.exists(ollama_exe) or bool(shutil.which("ollama"))
            models = []
            online = False
            try:
                import socket
                sock = socket.create_connection(("127.0.0.1", 11434), timeout=0.15)
                sock.close()
                code, res = http_json("http://127.0.0.1:11434/api/tags", timeout=0.8)
                if code == 200 and isinstance(res, dict):
                    online = True
                    models = [m.get("name") for m in res.get("models", [])]
            except Exception:
                online = False

            spidey_models = [
                {"id": "spidey-core-8b", "alias": "Peter Parker Prime", "desc": "Screenplay, dialogue & 30s creative storyboarding", "base": "llama3.1:8b / qwen2.5:7b"},
                {"id": "spider-sense-vision", "alias": "Miles Morales Vision", "desc": "Visual scene prompts, cinematography & lighting cues", "base": "llava / llama3.2-vision"},
                {"id": "symbiote-uncensored-7b", "alias": "Venom Lethal Protector", "desc": "Dark, intense battle choreography & gritty action scripts", "base": "dolphin / deepseek-r1"},
                {"id": "web-slinger-fast-3b", "alias": "ThinkPad Low-RAM Edition", "desc": "Lightweight 3B model tuned for 0% CPU lag on 8 GB RAM", "base": "llama3.2:3b / gemma2:2b"},
                {"id": "spidey-2099-quantum", "alias": "Miguel O'Hara Cyber-Weaver", "desc": "Flow pipeline timing, video frame interpolation formulas", "base": "command-r / deepseek"}
            ]

            self.send_json({
                "online": online,
                "installed": installed,
                "exe": ollama_exe,
                "active_models": models,
                "spidey_roster": spidey_models
            })
            return

        if path == "/api/status":
            self.send_json({
                "app": "Spidey AI",
                "mode": "cloud-relay",
                "local_engine": "disabled (low-RAM mode)",
                "drive_path": str(BASE_DIR),
                "ffmpeg": bool(FFMPEG_BIN),
                "keys": {
                    "gemini": bool(GEMINI_API_KEY),
                    "gemini_masked": mask_key(GEMINI_API_KEY),
                    "kie": bool(KIE_API_KEY),
                    "kie_masked": mask_key(KIE_API_KEY),
                },
            })
            return

        if path == "/api/kie/credit":
            if not KIE_API_KEY:
                self.send_json({"code": 401, "msg": "KIE_API_KEY not configured"}, status=401)
                return
            try:
                status, data = http_json(
                    "https://api.kie.ai/api/v1/chat/credit",
                    headers={"Authorization": f"Bearer {KIE_API_KEY}"},
                    timeout=12,
                )
                self.send_json(data, status=status)
            except Exception as e:
                self.send_json({"code": 500, "msg": str(e)}, status=500)
            return

        if path == "/api/kie/task-status":
            params = urllib.parse.parse_qs(parsed.query)
            task_id = params.get("taskId", [""])[0]
            if not task_id:
                self.send_json({"code": 400, "msg": "Missing taskId"}, status=400)
                return
            try:
                status, data = http_json(
                    f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={urllib.parse.quote(task_id)}",
                    headers={"Authorization": f"Bearer {KIE_API_KEY}"},
                    timeout=15,
                )
                self.send_json(data, status=status)
            except Exception as e:
                self.send_json({"code": 500, "msg": str(e)}, status=500)
            return

        if path == "/api/connectors":
            conn_file = BASE_DIR / "connectors.json"
            default_conns = {
                "airtable": False,
                "box": False,
                "dropbox": False,
                "frameio": False,
                "googleads": False,
                "googledrive": True,
                "vercel": True,
                "github": True
            }
            if conn_file.exists():
                try:
                    data = json.loads(conn_file.read_text(encoding="utf-8"))
                    default_conns.update(data)
                except Exception:
                    pass
            self.send_json({"connectors": default_conns})
            return

        if path == "/api/videos":
            items = []
            for p in sorted(VIDEOS_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
                if p.suffix.lower() in (".mp4", ".webm"):
                    items.append({
                        "name": p.name,
                        "url": f"/videos/{urllib.parse.quote(p.name)}",
                        "size_mb": round(p.stat().st_size / (1024 * 1024), 2),
                        "modified": int(p.stat().st_mtime),
                    })
            self.send_json({"videos": items})
            return

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            html_bytes = (BASE_DIR / "index.html").read_bytes()
            self.send_header("Content-Length", str(len(html_bytes)))
            self.end_headers()
            self.wfile.write(html_bytes)
            return

        super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            payload = {}

        if self.path == "/api/ollama/start":
            ollama_exe = r"C:\Users\T470s\AppData\Local\Programs\Ollama\ollama.exe"
            if not os.path.exists(ollama_exe):
                ollama_exe = shutil.which("ollama")
            if not ollama_exe:
                self.send_json({"error": "Ollama executable not found"}, status=404)
                return
            try:
                creation_flags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
                subprocess.Popen([ollama_exe, "serve"], creationflags=creation_flags)
                self.send_json({"status": "starting", "message": "Ollama background service launched on port 11434"})
            except Exception as e:
                self.send_json({"error": f"Failed to launch Ollama: {e}"}, status=500)
            return

        if self.path in ("/api/ollama/generate", "/api/engine/direct"):
            prompt = payload.get("prompt", "").strip() or "Cinematic slow motion shot of a lone samurai walking through a misty forest"
            try:
                if hydrogen_video_engine:
                    spec = hydrogen_video_engine.direct_with_gemini_4_hydrogen(prompt, api_key=GEMINI_API_KEY)
                else:
                    spec = {"title": "Hydrogen Scene", "acts": []}
                self.send_json({
                    "text": f"🎬 [Google Hydrogen Director - Gemini 4]\nDirected Cinematic Sequence: '{spec.get('title')}'",
                    "source": "gemini-4-hydrogen",
                    "model": "gemini-4-hydrogen",
                    "specification": spec,
                    "scenes": spec.get("acts", []),
                    "duration": 30
                })
            except Exception as e:
                self.send_json({"error": f"Director failed: {e}"}, status=500)
            return

        if self.path == "/api/chat":
            prompt = payload.get("prompt", "").strip()
            system_prompt = payload.get("system_prompt", "You are Spidey AI, a fast, helpful creative & video assistant.")
            model = payload.get("model", "gemini-3.8-flash")
            if model not in ("gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3-flash-preview"):
                model = "gemini-3.8-flash"

            if not prompt:
                self.send_json({"error": "Prompt is empty"}, status=400)
                return

            if GEMINI_API_KEY:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                    body = {
                        "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser: {prompt}"}]}]
                    }
                    status, res = http_json(url, method="POST", payload=body, timeout=30)
                    if status == 200 and res.get("candidates"):
                        reply = res["candidates"][0]["content"]["parts"][0]["text"]
                        self.send_json({"reply": reply, "engine": model})
                        return
                except Exception:
                    pass

            # Free Pollinations fallback
            try:
                encoded = urllib.parse.quote(f"{system_prompt}\n\n{prompt}")
                req = urllib.request.Request(
                    f"https://text.pollinations.ai/{encoded}",
                    headers={"User-Agent": "SpideyAI/1.0"},
                )
                with urllib.request.urlopen(req, timeout=25) as r:
                    self.send_json({"reply": r.read().decode("utf-8", errors="replace"), "engine": "Pollinations Free"})
                    return
            except Exception as e:
                self.send_json({"error": f"Chat failed: {e}"}, status=500)
            return

        if self.path == "/api/tts":
            text = payload.get("text", "").strip()
            voice = payload.get("voice", "Kore")
            save_file = bool(payload.get("save", False))
            if not text:
                self.send_json({"error": "No text provided"}, status=400)
                return
            if not GEMINI_API_KEY:
                self.send_json({"error": "GEMINI_API_KEY not set", "fallback_tts": True}, status=200)
                return
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent?key={GEMINI_API_KEY}"
                body = {
                    "contents": [{"parts": [{"text": text[:1500]}]}],
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}
                        },
                    },
                }
                status, res = http_json(url, method="POST", payload=body, timeout=30)
                if status == 200 and res.get("candidates"):
                    inline = res["candidates"][0]["content"]["parts"][0]["inlineData"]
                    audio_b64 = inline["data"]
                    mime = inline.get("mimeType", "audio/wav")
                    saved_url = None
                    if save_file:
                        fname = f"spidey_voice_{int(time.time())}.wav"
                        (AUDIO_DIR / fname).write_bytes(base64.b64decode(audio_b64))
                        saved_url = f"/audio/{fname}"
                    self.send_json({
                        "audio_base64": audio_b64,
                        "mime_type": mime,
                        "saved_url": saved_url,
                    })
                    return
                self.send_json({"error": res.get("error", {}).get("message", "TTS failed"), "fallback_tts": True}, status=200)
            except Exception as e:
                self.send_json({"error": str(e), "fallback_tts": True}, status=200)
            return

        if self.path == "/api/kie/create-task":
            if not KIE_API_KEY:
                self.send_json({"code": 401, "msg": "KIE_API_KEY is not configured in .env"}, status=401)
                return
            model = payload.get("model", "wan/2-6-text-to-video")
            input_data = payload.get("input", {})
            task_payload = {"model": model, "input": input_data}
            try:
                status, data = http_json(
                    "https://api.kie.ai/api/v1/jobs/createTask",
                    method="POST",
                    payload=task_payload,
                    headers={"Authorization": f"Bearer {KIE_API_KEY}"},
                    timeout=30,
                )
                self.send_json(data, status=status)
            except Exception as e:
                self.send_json({"code": 500, "msg": str(e)}, status=500)
            return

        if self.path == "/api/save-video":
            video_url = payload.get("url", "").strip()
            prefix = re.sub(r"[^a-zA-Z0-9_-]", "", payload.get("prefix", "spidey_ai")) or "spidey_ai"
            if not video_url.startswith("http"):
                self.send_json({"error": "Invalid video URL"}, status=400)
                return
            try:
                fname = f"{prefix}_{int(time.time())}.mp4"
                out_path = VIDEOS_DIR / fname
                req = urllib.request.Request(video_url, headers={"User-Agent": "SpideyAI/1.0"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    out_path.write_bytes(r.read())
                self.send_json({"saved": True, "name": fname, "url": f"/videos/{fname}", "path": str(out_path)})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        if self.path == "/api/render-cinema":
            if not FFMPEG_BIN:
                self.send_json({"error": "FFmpeg not found on system. Use browser WebM export instead."}, status=400)
                return
            scenes = payload.get("scenes", [])
            ratio = payload.get("ratio", "16:9")
            audio_b64 = payload.get("audio_base64", "")
            if not scenes:
                self.send_json({"error": "No scenes supplied"}, status=400)
                return

            ts = int(time.time())
            width, height = (720, 1280) if ratio == "9:16" else ((1024, 1024) if ratio == "1:1" else (1280, 720))
            clips = []
            try:
                # Support 30s+ multi-scene cinema (up to 12 scenes, e.g. 6 scenes x 5s = 30s)
                for idx, sc in enumerate(scenes[:12]):
                    img_url = sc.get("image", "")
                    dur = float(sc.get("duration", 5))
                    motion = sc.get("motion", "zoom_in")
                    img_file = TEMP_DIR / f"f_{ts}_{idx}.jpg"
                    clip_file = TEMP_DIR / f"c_{ts}_{idx}.mp4"

                    downloaded = False
                    if img_url.startswith("http"):
                        try:
                            req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                            with urllib.request.urlopen(req, timeout=18) as r:
                                img_file.write_bytes(r.read())
                                downloaded = img_file.stat().st_size > 1000
                        except Exception:
                            downloaded = False

                    if not downloaded:
                        subprocess.run(
                            [FFMPEG_BIN, "-y", "-f", "lavfi", "-i", f"color=c=0x0d111d:s={width}x{height}:d=1", "-frames:v", "1", str(img_file)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                        )

                    frames = max(25, int(dur * 25))
                    if "pan" in motion.lower():
                        zp = f"zoompan=z=1.12:x='if(lte(on,1),(iw-iw/zoom)/2,x+0.7)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}"
                    else:
                        zp = f"zoompan=z='min(zoom+0.0009,1.18)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}"

                    vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},{zp},format=yuv420p"
                    subprocess.run(
                        [
                            FFMPEG_BIN, "-y", "-loop", "1", "-i", str(img_file),
                            "-vf", vf, "-t", str(dur), "-r", "25",
                            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                            str(clip_file),
                        ],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                    )
                    clips.append(clip_file)

                concat_txt = TEMP_DIR / f"list_{ts}.txt"
                concat_txt.write_text("\n".join(f"file '{c.as_posix()}'" for c in clips), encoding="utf-8")

                merged_vid = TEMP_DIR / f"merged_{ts}.mp4"
                subprocess.run(
                    [FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(merged_vid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                )

                out_name = f"spidey_cinema_{ts}.mp4"
                out_path = VIDEOS_DIR / out_name

                if audio_b64:
                    aud_file = TEMP_DIR / f"aud_{ts}.wav"
                    aud_file.write_bytes(base64.b64decode(audio_b64))
                    subprocess.run(
                        [
                            FFMPEG_BIN, "-y", "-i", str(merged_vid), "-i", str(aud_file),
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", str(out_path),
                        ],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                    )
                else:
                    shutil.move(str(merged_vid), str(out_path))

                # Cleanup temp files
                for f in TEMP_DIR.glob(f"*_{ts}*"):
                    f.unlink(missing_ok=True)

                self.send_json({"ok": True, "name": out_name, "url": f"/videos/{out_name}", "path": str(out_path)})
            except Exception as e:
                self.send_json({"error": f"Render failed: {e}"}, status=500)
            return

        if self.path == "/api/connectors/toggle":
            conn_id = payload.get("id")
            conn_file = BASE_DIR / "connectors.json"
            conns = {}
            if conn_file.exists():
                try:
                    conns = json.loads(conn_file.read_text(encoding="utf-8"))
                except Exception:
                    conns = {}
            current = conns.get(conn_id, False)
            conns[conn_id] = not current
            conn_file.write_text(json.dumps(conns, indent=2), encoding="utf-8")
            self.send_json({"ok": True, "id": conn_id, "connected": conns[conn_id]})
            return

        if self.path == "/api/upload":
            filename = payload.get("filename", f"upload_{int(time.time())}.png")
            file_b64 = payload.get("data_base64", "")
            if not file_b64:
                self.send_json({"error": "No file data provided"}, status=400)
                return
            if "," in file_b64:
                file_b64 = file_b64.split(",", 1)[1]
            out_file = VIDEOS_DIR / filename
            try:
                out_file.write_bytes(base64.b64decode(file_b64))
                self.send_json({
                    "ok": True,
                    "name": filename,
                    "url": f"/videos/{urllib.parse.quote(filename)}",
                    "size_mb": round(out_file.stat().st_size / (1024 * 1024), 2)
                })
            except Exception as e:
                self.send_json({"error": f"Upload failed: {e}"}, status=500)
            return

        if self.path in ("/api/engine/hydrogen-direct", "/api/hydrogen/direct"):
            prompt = payload.get("prompt", "Cinematic slow motion shot of a lone samurai walking through a misty forest")
            higgsfield = payload.get("higgsfield", {})
            try:
                if hydrogen_video_engine:
                    spec = hydrogen_video_engine.direct_with_gemini_4_hydrogen(prompt, api_key=GEMINI_API_KEY, higgsfield=higgsfield)
                else:
                    spec = {"title": "Hydrogen Scene", "acts": []}
                self.send_json({"ok": True, "specification": spec})
            except Exception as e:
                self.send_json({"error": f"Hydrogen direct failed: {e}"}, status=500)
            return

        if self.path in ("/api/engine/hydrogen-video", "/api/engine/create-30s-video", "/api/hydrogen/generate"):
            if not FFMPEG_BIN:
                self.send_json({"error": "FFmpeg engine not found on system. Check installation."}, status=500)
                return
            prompt = payload.get("prompt", "Cinematic slow motion shot of a lone samurai walking through a misty forest")
            style = payload.get("style", "samurai_cinema")

            try:
                if hydrogen_video_engine:
                    res = hydrogen_video_engine.render_hydrogen_film_mp4(prompt=prompt, style=style)
                    self.send_json(res)
                else:
                    self.send_json({"error": "Hydrogen video engine module not initialized"}, status=500)
            except Exception as e:
                self.send_json({"error": f"Hydrogen render failed: {e}"}, status=500)
            return

        if self.path == "/api/connectors/toggle":
            conn_id = payload.get("id")
            conn_file = BASE_DIR / "connectors.json"
            conns = {}
            if conn_file.exists():
                try:
                    conns = json.loads(conn_file.read_text(encoding="utf-8"))
                except Exception:
                    conns = {}
            current = conns.get(conn_id, False)
            conns[conn_id] = not current
            conn_file.write_text(json.dumps(conns, indent=2), encoding="utf-8")
            self.send_json({"ok": True, "id": conn_id, "connected": conns[conn_id]})
            return

        if self.path == "/api/upload":
            filename = payload.get("filename", f"upload_{int(time.time())}.png")
            file_b64 = payload.get("data_base64", "")
            if not file_b64:
                self.send_json({"error": "No file data provided"}, status=400)
                return
            if "," in file_b64:
                file_b64 = file_b64.split(",", 1)[1]
            out_file = VIDEOS_DIR / filename
            try:
                out_file.write_bytes(base64.b64decode(file_b64))
                self.send_json({
                    "ok": True,
                    "name": filename,
                    "url": f"/videos/{urllib.parse.quote(filename)}",
                    "size_mb": round(out_file.stat().st_size / (1024 * 1024), 2)
                })
            except Exception as e:
                self.send_json({"error": f"Upload failed: {e}"}, status=500)
            return



        self.send_json({"error": "Endpoint not found"}, status=404)


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", "8080"))
    server = ThreadingHTTPServer(("127.0.0.1", PORT), SpideyHandler)
    print("==================================================")
    print("  SPIDEY AI — Cloud Relay Online (Low-RAM Mode)")
    print(f"  Home Page : http://localhost:{PORT}")
    print(f"  Drive Path: {BASE_DIR}")
    print("==================================================")
    server.serve_forever()
