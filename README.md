# 🕷️ Spidey AI — Visionary 30s Video Creation Studio

> **Ultra-premium web-based AI video creation studio powered by Gemini 3.8 and Google Drive storage.**
> Featuring **The Amazing Spider-Man** full-time web-swinging animation, interactive **Spidey vs Venom Symbiote Clash Arena**, and zero-cost 30-second multi-scene video engine.

---

## ⚡ Key Highlights

- **30-Second Minimum Free Cinema Engine:** Automatically generates 6-act to 12-act storyboards, renders realistic visual frames, narrates with Gemini 3.8 neural TTS, applies Ken Burns cinematic camera movement, and exports full HD MP4/WebM videos straight to Google Drive.
- **Starring The Amazing Spider-Man & Venom:**
  - Ambient Web-Swinger: The Amazing Spider-Man swings full-time across the top bar with realistic physics and interactive acrobatics.
  - Symbiote Duel Arena: Interactive battleground where Spider-Man and Venom fight with web strikes, symbiote tendrils, and dynamic HP meters.
  - 1-Click "Make 30s Movie of this Duel": Direct generation of a 30s cinematic clash film starring Spider-Man and Venom.
- **Zero-Lag Architecture:** Run completely from Google Drive (`G:\My Drive\Spidey-AI`) with 0% idle CPU and zero laptop hanging on lightweight PCs (8 GB RAM / ThinkPad T470s).
- **Lumina AI + Gemini Studio Aesthetics:** Ultra-clean glassmorphic UI styled with crisp white, neon emerald green (`#00ff87`), and symbiote accents.
- **Strict Vertical Spacing Scale:** 6-token harmonic design system (`4px, 8px, 12px, 16px, 24px, 48px`).

---

## 🚀 Quick Start (Local with Google Drive)

Double click `start_spidey_ai.bat` or run:

```bash
python -B server.py
```

Then visit:
```
http://localhost:8080
```

---

## 🌐 Deploy to Vercel (Free)

The frontend is fully static and pre-configured for Vercel:

1. Push this repository to your GitHub:
   ```bash
   git remote add origin https://github.com/<YOUR_USER>/spidey-ai.git
   git push -u origin main
   ```
2. Log into [vercel.com](https://vercel.com) and click **"Add New Project"**.
3. Select your `spidey-ai` repository and click **Deploy**.
4. Your site will be live instantly on `https://spidey-ai.vercel.app`!

---

## ☁️ Deploy to Google Cloud Run (Free Tier)

A production `Dockerfile` is included in this repository. To deploy free on Google Cloud Run (2,000,000 free requests per month):

```bash
gcloud run deploy spidey-ai --source . --port 8080 --allow-unauthenticated
```

---

## 🎬 Architecture & Folders

- `index.html` — Lumina AI & Gemini AI Studio frontend interface
- `server.py` — Python lightweight relay & FFmpeg multi-scene video concatenator
- `assets/` — High-definition Amazing Spider-Man and Venom photorealistic character assets
  - `spidey_hero.jpg` — High-resolution Amazing Spider-Man swinging asset
  - `venom_beast.webp` — High-resolution Venom roaring symbiote asset
- `videos/` — Rendered MP4 & WebM cinematic movies stored in Google Drive
- `vercel.json` — Vercel static hosting configuration
- `Dockerfile` — Google Cloud container deployment

---

*Built with ❤️ as a brother for the ultimate Spidey AI experience.*
