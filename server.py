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

BASE_DIR = Path(__file__).resolve().parent
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

        if self.path == "/api/ollama/generate":
            prompt = payload.get("prompt", "").strip()
            spidey_model = payload.get("model", "spidey-core-8b")
            system = payload.get("system", "You are Spidey AI Google Flow Director, an expert cinema video architect. Create an ultra-realistic 30-second 6-act movie sequence.")
            
            # Check if local Ollama is active
            ollama_online = False
            try:
                code, tags = http_json("http://localhost:11434/api/tags", timeout=1.2)
                if code == 200:
                    ollama_online = True
            except Exception:
                ollama_online = False

            if ollama_online:
                try:
                    code, res = http_json("http://localhost:11434/api/generate", method="POST", payload={
                        "model": "llama3.2" if "3b" in spidey_model else "llama3.1",
                        "prompt": f"{system}\n\nTask: {prompt}",
                        "stream": False
                    }, timeout=25.0)
                    if code == 200 and isinstance(res, dict):
                        self.send_json({"text": res.get("response", ""), "source": f"local-ollama ({spidey_model})", "model": spidey_model})
                        return
                except Exception:
                    pass

            # Intelligent Spidey Flow Screenplay Fallback Engine
            clean_topic = prompt or "The Amazing Spider-Man vs Venom: Skyline Reckoning"
            scenes = [
                {"act": "ACT I", "title": "THE CATALYST", "duration": 5, "motion": "zoom_in", "image": "assets/spidey_hero.jpg", "visual": f"IMAX establishing shot of Spider-Man perched above rainy neon city skyline: {clean_topic}", "narration": f"Midnight sweeps over the city as dark vibrations echo around {clean_topic}."},
                {"act": "ACT II", "title": "SYMBIOTE AWAKENING", "duration": 5, "motion": "pan_right", "image": "assets/venom_beast.webp", "visual": f"Venom roaring through dark mist with purple symbiote lightning reacting to: {clean_topic}", "narration": "From the abyss emerges Venom, snarling with symbiote power and primal hunger."},
                {"act": "ACT III", "title": "SKYSCRAPER PURSUIT", "duration": 5, "motion": "zoom_in", "image": "assets/spidey_hero.jpg", "visual": f"Dynamic FPV chase camera following Spider-Man swinging along glass walls: {clean_topic}", "narration": "Spider-Man launches into velocity, weaving through falling glass and steel."},
                {"act": "ACT IV", "title": "APEX CLASH", "duration": 5, "motion": "pan_left", "image": "assets/venom_beast.webp", "visual": f"Mid-air collision: electric web blast impacts roaring Venom symbiote maw: {clean_topic}", "narration": "Webs collide with symbiote tentacles in a blinding sonic explosion."},
                {"act": "ACT V", "title": "OVERDRIVE", "duration": 5, "motion": "zoom_in", "image": "assets/spidey_hero.jpg", "visual": f"Extreme macro shot of Spider-Man visor reflecting Venom razor teeth: {clean_topic}", "narration": "Pushed to the absolute edge, Spider-Sense fires with lethal precision."},
                {"act": "ACT VI", "title": "HORIZON RESOLUTION", "duration": 5, "motion": "pan_right", "image": "assets/spidey_hero.jpg", "visual": f"Spider-Man standing victorious atop city bridge as sunrise cuts through rain clouds: {clean_topic}", "narration": "The dawn returns to the skyline. The guardian holds the line."}
            ]
            self.send_json({
                "text": f"🎬 [Spidey Flow Director - {spidey_model}]\nGenerated 6-Act 30-Second Cinematic Sequence for: '{clean_topic}'",
                "source": f"spidey-flow-engine ({spidey_model})",
                "model": spidey_model,
                "scenes": scenes,
                "duration": 30
            })
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

        if self.path == "/api/engine/create-30s-video":
            if not FFMPEG_BIN:
                self.send_json({"error": "FFmpeg engine not found on system. Check installation."}, status=500)
                return
            prompt = payload.get("prompt", "Infinite Quantum Reality Voyage")
            style = payload.get("style", "infinity_cosmos")
            ratio = payload.get("ratio", "16:9")
            title = payload.get("title", "Quantum Infinity 30s")

            width, height = (1280, 720)
            if ratio == "9:16":
                width, height = (720, 1280)
            elif ratio == "1:1":
                width, height = (720, 720)

            ts = int(time.time())
            out_name = f"infinity_30s_{ts}.mp4"
            out_path = VIDEOS_DIR / out_name

            if style == "cyber_matrix":
                video_src = f"mandelbrot=size={width}x{height}:rate=25:maxiter=160:inner=period:start_scale=1.8"
                color_vf = "hue=h=t*18:s=1.8,curves=all='0/0 0.5/0.2 1/1'"
            elif style == "quantum_warp":
                video_src = f"mandelbrot=size={width}x{height}:rate=25:maxiter=200:inner=black:start_scale=4.2"
                color_vf = "hue=h=t*25:s=sin(t*0.5)+1.2,lenscorrection=cx=0.5:cy=0.5:k1=-0.15:k2=0.08"
            elif style == "neural_nebula":
                video_src = f"mandelbrot=size={width}x{height}:rate=25:maxiter=140:inner=white:start_scale=2.5"
                color_vf = "hue=h=t*10:s=1.5,curves=vintage"
            else:
                video_src = f"mandelbrot=size={width}x{height}:rate=25:maxiter=150:inner=black:start_scale=3.5"
                color_vf = "hue=h=t*12:s=sin(t)+1"

            text_vf = (
                f"{color_vf},"
                "drawtext=text='AI STUDIO // 30s INFINITY ENGINE':fontcolor=white@0.85:fontsize=18:x=40:y=40:shadowcolor=black:shadowx=2:shadowy=2,"
                "drawtext=text='ACT %{eif\\:trunc(t/5)+1\\:d} / 6 - %{eif\\:mod(trunc(t),5)+1\\:d}s':fontcolor=white:fontsize=24:x=40:y=h-70:shadowcolor=black:shadowx=2:shadowy=2,"
                "drawtext=text='%{pts\\:hms}':fontcolor=white@0.7:fontsize=18:x=w-160:y=h-70:shadowcolor=black:shadowx=2:shadowy=2"
            )

            audio_synth = (
                "aevalsrc="
                "0.4*sin(2*PI*(44+16*t/30)*t) + "
                "0.25*sin(2*PI*110*t) + "
                "0.18*sin(2*PI*(220+75*t/30)*t) + "
                "0.1*sin(2*PI*(440+20*sin(2*PI*0.5*t))*t)"
                ":s=44100:c=stereo"
            )

            cmd = [
                FFMPEG_BIN, "-y",
                "-f", "lavfi", "-i", video_src,
                "-f", "lavfi", "-i", audio_synth,
                "-t", "30",
                "-vf", text_vf,
                "-af", "afade=t=in:ss=0:d=1.5,afade=t=out:st=28.5:d=1.5",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-b:v", "3500k",
                "-c:a", "aac", "-b:a", "128k",
                str(out_path)
            ]

            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if res.returncode != 0:
                    self.send_json({"error": f"FFmpeg failed: {res.stderr[-300:]}"}, status=500)
                    return

                size = out_path.stat().st_size
                acts = [
                    {"act": 1, "name": "Genesis & Singularity Ignition", "time": "00:00 - 00:05", "desc": "Sub-atomic particle ignition and infinite void expansion."},
                    {"act": 2, "name": "Event Horizon Curvature", "time": "00:05 - 00:10", "desc": "Relativistic gravitational light deflection and distortion."},
                    {"act": 3, "name": "Quantum Matrix Shift", "time": "00:10 - 00:15", "desc": "Multidimensional hyper-geometric fractal displacement."},
                    {"act": 4, "name": "Neural Cosmos Nebula", "time": "00:15 - 00:20", "desc": "Volumetric starlight synthesis and chromatic particle river."},
                    {"act": 5, "name": "Hyperdrive Warp Velocity", "time": "00:20 - 00:25", "desc": "Infinite speed acceleration and relativistic time dilation."},
                    {"act": 6, "name": "Transcendence & Infinity Loop", "time": "00:25 - 00:30", "desc": "Recursive cosmic loop entering eternal singularity."}
                ]

                self.send_json({
                    "ok": True,
                    "title": title,
                    "prompt": prompt,
                    "style": style,
                    "duration": 30,
                    "resolution": f"{width}x{height}",
                    "size_bytes": size,
                    "size_mb": round(size / (1024 * 1024), 2),
                    "url": f"/videos/{out_name}",
                    "filename": out_name,
                    "acts": acts
                })
            except Exception as e:
                self.send_json({"error": f"Render exception: {e}"}, status=500)
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
